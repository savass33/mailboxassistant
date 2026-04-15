import json
import re
from colorama import Fore, Style
from src.services.gmail_service import GmailService
from src.services.llm_service import LLMService
from src.services.telegram_service import TelegramService
from src.services.db_service import DBService

class NexusAgent:
    def __init__(self):
        self.gmail = GmailService()
        self.llm = LLMService()
        self.telegram = TelegramService()
        self.db = DBService()

    def _broadcast(self, text: str, chat_id: int = None):
        """Dispara a saída tanto para o terminal quanto para o Telegram, se houver chat_id."""
        print(f"\n{Fore.CYAN}╔════════════════════ NEXUS SYSTEM ════════════════════╗{Style.RESET_ALL}")
        print(text)
        print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
        
        if chat_id:
            self.telegram.send_message(chat_id, text)

    def process_telegram_command(self, chat_id: int, user_text: str):
        """O Cérebro Roteador (Intent Parser) - Interpreta linguagem natural do Telegram."""
        self._broadcast("⏳ *Interpretando Comando Tático...*", chat_id)
        
        router_prompt = f"""Analise a intenção do usuário: "{user_text}"

Retorne APENAS um JSON plano (sem markdown) com estes campos:
- action: "triage", "news", "deepdive" ou "chat".
- query: Busca Gmail (ex: "from:google") ou "". Use apenas se for "deepdive".
- mark_read: true ou false. Marque true se o usuário pedir para marcar como lido, limpar ou apagar notificação.

EXEMPLO DE RESPOSTA (Não copie o conteúdo, apenas o formato):
{{"action": "triage", "query": "", "mark_read": true}}
"""
        
        try:
            print(f"{Fore.YELLOW}[*] Nexus Engine: Roteando intenção via LLM...{Style.RESET_ALL}")
            intent_response = self.llm.analyze("Responda APENAS JSON puro.", router_prompt)
            print(f"DEBUG LLM Router: {intent_response}")
            
            match = re.search(r'\{.*?\}', intent_response, re.DOTALL)
            if not match: raise ValueError("JSON não encontrado.")
            intent = json.loads(match.group(0).strip())
            
            action = intent.get("action", "chat")
            query = intent.get("query", "")
            # Limpa lixo que a IA costuma colocar na query se for triage
            if action != "deepdive": query = ""
            mark_read = intent.get("mark_read", False)
            
            print(f"{Fore.GREEN}[+] Intenção: {action} | Query: {query} | MarkRead: {mark_read}{Style.RESET_ALL}")

            if action == "triage":
                self.triage_unread(chat_id, mark_read)
            elif action == "news":
                self.process_newsletters(chat_id, mark_read)
            elif action == "deepdive":
                self.deep_dive(query, chat_id, mark_read)
            else:
                self._broadcast("🤖 **NEXUS:** Como posso otimizar sua caixa de entrada hoje?", chat_id)
                
        except Exception as e:
            self._broadcast(f"❌ Erro no roteamento: {e}", chat_id)

    def triage_unread(self, chat_id: int = None, mark_read: bool = False):
        print(f"{Fore.YELLOW}[*] Nexus Engine: Iniciando Triage Protocol...{Style.RESET_ALL}")
        self._broadcast("🔎 *Buscando e classificando sua caixa de entrada...*", chat_id)
        
        emails = self.gmail.fetch_emails(query='is:unread', limit=10)
        if not emails:
            self._broadcast("📭 STATUS: Caixa de entrada sincronizada.", chat_id)
            return

        email_text = "\n".join([f"De: {e['from']} | Assunto: {e['subject']} | Snippet: {e['snippet']}" for e in emails])
        
        system_prompt = """Você é um analista executivo de e-mails de alta performance. 
Sua tarefa é classificar os e-mails reais do usuário seguindo estas regras de negócio:

CATEGORIAS E TAGS:
🔴 | CRÍTICO | Alertas de Segurança, Mensagens da Chefia, Processos Admissionais/Emprego (ex: Gupy) e Prazos de Entregas/Hackathons.
🔵 | FINANCEIRO | Bancos (Inter, Nubank), Relatórios de Gastos (Pierre), Comprovantes e Pix.
🟢 | NOTÍCIAS | Newsletters (Filipe Deschamps, etc), Artigos e Curadorias.
⚪ | NOISE | Promoções, Spam disfarçado, Recibos de compras menores e avisos genéricos.

FORMATO DE RESPOSTA (Obrigatório):
TAG | CATEGORIA | CONTEÚDO RESUMIDO

Exemplo:
🔴 | CRÍTICO | Gupy: Documentos pendentes para sua admissão.
🔵 | FINANCEIRO | Inter: Relatório de cashback disponível.

Seja extremamente criterioso. Use apenas dados reais."""

        try:
            response = self.llm.analyze("Classifique os e-mails reais usando as novas categorias: CRÍTICO, FINANCEIRO, NOTÍCIAS, NOISE.", system_prompt + "\n\nEMAILS REAIS:\n" + email_text)
            print(f"DEBUG LLM Triage:\n{response}")
            
            lines = [l.strip() for l in response.strip().split('\n') if '|' in l]
            
            if not lines:
                raise ValueError("Ollama não seguiu o formato de categorias.")

            self._broadcast("<b>📋 RELATÓRIO DE TRIAGEM ATUALIZADO</b>", chat_id)
            
            # Divide as linhas em bubbles de 3
            for i in range(0, len(lines), 3):
                chunk = lines[i:i+3]
                bubble = ""
                for line in chunk:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        tag, cat, content = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        bubble += f"{tag} <b>{cat}</b>\n{content}\n\n"
                
                if bubble:
                    self.telegram.send_message(chat_id, bubble)

            if mark_read:
                print(f"{Fore.MAGENTA}[*] Gmail: Marcando {len(emails)} emails como lidos...{Fore.RESET}")
                self.gmail.mark_as_read([e['id'] for e in emails])
                self._broadcast("🧹 *Limpeza concluída: Emails marcados como lidos.*", chat_id)

        except Exception as e:
            self._broadcast(f"❌ Falha no processamento: {e}", chat_id)

    def deep_dive(self, search_query: str, chat_id: int = None, mark_read: bool = False):
        print(f"{Fore.YELLOW}[*] Nexus Engine: Deep Dive em {search_query}...{Style.RESET_ALL}")
        self._broadcast(f"🕵️‍♂️ *Infiltrando e-mails: `{search_query}`...*", chat_id)
        
        final_query = search_query if "is:unread" in search_query else f"is:unread {search_query}"
        emails = self.gmail.fetch_emails(query=final_query, limit=1)
        
        if not emails:
            self._broadcast(f"⚠️ Nenhum e-mail não lido para: `{search_query}`.", chat_id)
            return
            
        email = emails[0]
        content = f"De: {email['from']}\nAssunto: {email['subject']}\nCorpo:\n{email['body'][:3000]}" 

        system_prompt = """Você é o Nexus. Faça um resumo PROFUNDO e INFORMATIVO.
Estrutura:
📌 **CONTEXTO**: O que está acontecendo?
🧠 **ANÁLISE**: Por que isso é importante? Detalhe os pontos técnicos ou fatos.
⚡ **PRÓXIMOS PASSOS**: O que o usuário deve fazer?
📝 **SUGESTÃO DE RESPOSTA**: Texto pronto para enviar.

Seja técnico e direto. Use negrito."""

        response = self.llm.analyze(system_prompt, content)
        self._broadcast(f"📦 **DETALHES DO E-MAIL**\n\n{response}", chat_id)
        
        if mark_read:
            self.gmail.mark_as_read([email['id']])
            self._broadcast(f"🧹 *Email de '{email['from']}' marcado como lido.*", chat_id)

    def process_newsletters(self, chat_id: int = None, mark_read: bool = False):
        print(f"{Fore.YELLOW}[*] Nexus Engine: Newsletter Extraction...{Style.RESET_ALL}")
        self._broadcast("📰 *Destilando Newsletters. Foco em IA e Mercado...*", chat_id)
        
        emails = self.gmail.fetch_emails(query='is:unread (unsubscribe OR "cancelar inscrição")', limit=10)
        if not emails:
            self._broadcast("📭 STATUS: Nenhuma nova Newsletter identificada na fila.", chat_id)
            return

        email_text = "\n\n---\n\n".join([f"De: {e['from']}\nAssunto: {e['subject']}\nCorpo:\n{e['body'][:1500]}" for e in emails])

        system_prompt = """Você é o 'Nexus', curador de inteligência de mercado.

DIRETRIZES PARA NEWSLETTERS:
- Extraia APENAS fatos cruciais focados em: IA, Programação, Mercado, Cripto.
- Formate a saída em Bullet Points rápidos (máx. 2 linhas cada).

Estrutura OBRIGATÓRIA:
📰 **[Nome do Remetente / Newsletter]**
- Fato importante 1
- Fato importante 2

Use espaços (\\n\\n) entre as diferentes newsletters. Sem enrolação."""

        response = self.llm.analyze(system_prompt, email_text)
        self._broadcast(response, chat_id)
        
        if mark_read:
            self.gmail.mark_as_read([e['id'] for e in emails])
            self._broadcast("🧹 *As newsletters acima foram marcadas como lidas.*", chat_id)
