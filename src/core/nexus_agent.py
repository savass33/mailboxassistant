import json
import re
from colorama import Fore, Style
from src.services.gmail_service import GmailService
from src.services.llm_service import LLMService
from src.services.telegram_service import TelegramService
from src.services.memory_service import MemoryService

class NexusAgent:
    def __init__(self):
        self.gmail = GmailService()
        self.llm = LLMService()
        self.telegram = TelegramService()
        self.memory = MemoryService()

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

Retorne APENAS um JSON plano (sem markdown) escolhendo UMA destas actions:
- "triage": ler, resumir ou ver a caixa de entrada de forma GERAL (vários e-mails).
- "deepdive": focar, ler ou resumir um e-mail ESPECÍFICO (ex: "o email do filipe", "do meu chefe").
- "news": ler ou focar apenas em newsletters/notícias gerais.
- "reply": responder a um e-mail.
- "sync_memory": sincronizar ou baixar e-mails para a memória.
- "ask_memory": perguntas sobre o passado ("quando comprei", "qual o valor de").
- "chat": conversa genérica fora do escopo de e-mails.

Campos adicionais do JSON:
- query: Busca Gmail se deepdive/reply (ex: "from:filipe"). Se "ask_memory", coloque a pergunta aqui.
- instruction: Instrução de resposta APENAS se for "reply".
- mark_read: true se pedir para marcar como lido, limpar ou apagar.

EXEMPLO DE RESPOSTA (Não copie o conteúdo, apenas siga a estrutura das chaves):
{{"action": "deepdive", "query": "from:filipe", "instruction": "", "mark_read": false}}
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
            instruction = intent.get("instruction", "")
            if action not in ["deepdive", "reply", "ask_memory"]: query = ""
            mark_read = intent.get("mark_read", False)
            
            print(f"{Fore.GREEN}[+] Intenção: {action} | Query: {query} | Instruction: {instruction} | MarkRead: {mark_read}{Style.RESET_ALL}")

            if action == "triage":
                self.triage_unread(chat_id, mark_read)
            elif action == "news":
                self.process_newsletters(chat_id, mark_read)
            elif action == "deepdive":
                self.deep_dive(query, chat_id, mark_read)
            elif action == "reply":
                self.reply_to_email(query, instruction, chat_id, mark_read)
            elif action == "sync_memory":
                self.sync_memory(chat_id)
            elif action == "ask_memory":
                self.ask_memory(query, chat_id)
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

        email_text = "\n".join([f"ID: {e['id']} | De: {e['from']} | Assunto: {e['subject']} | Resumo: {e['snippet']}" for e in emails])
        
        system_prompt = """Você é um classificador de e-mails robótico.
A sua saída deve ser APENAS LINHAS DE TEXTO. NÃO pule linhas extras. NÃO use negrito. NÃO faça observações. NÃO cumprimente.

Categorias e Tags:
🔴 | CRÍTICO | Alertas de Segurança, Chefia, Vagas/Gupy, Prazos.
🔵 | FINANCEIRO | Bancos (Inter), Gastos (Pierre), Pix.
🟢 | NOTÍCIAS | Newsletters (Filipe Deschamps), Artigos.
⚪ | NOISE | Outros, Spam, Promoções.

Formato OBRIGATÓRIO (Uma linha por e-mail, separada por pipe '|'):
TAG | CATEGORIA | Resumo curto do email

Exemplo correto:
🔴 | CRÍTICO | Alerta de segurança do Google na conta Savas.
⚪ | NOISE | Gasto de R$30 no cartão final 1234.

Use dados REAIS fornecidos abaixo."""

        try:
            response = self.llm.analyze("Classifique usando as categorias e o formato exato exigido.", system_prompt + "\n\nEMAILS REAIS:\n" + email_text)
            print(f"DEBUG LLM Triage:\n{response}")
            
            lines = [l.strip() for l in response.strip().split('\n') if '|' in l and len(l.split('|')) >= 3]
            
            if not lines:
                raise ValueError("Ollama não gerou linhas válidas com o caractere '|'.")

            self._broadcast("<b>📋 RELATÓRIO DE TRIAGEM ATUALIZADO</b>", chat_id)
            
            # Divide as linhas em bubbles de 3
            for i in range(0, len(lines), 3):
                chunk = lines[i:i+3]
                bubble = ""
                for line in chunk:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        tag, cat, content = parts[0].strip(), parts[1].strip(), "|".join(parts[2:]).strip()
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
        
        # Remove a limitação de "não lido" para Deep Dive. O usuário pode querer reler um e-mail.
        emails = self.gmail.fetch_emails(query=search_query, limit=1)
        
        if not emails:
            self._broadcast(f"⚠️ Nenhum e-mail localizado para a busca `{search_query}`.", chat_id)
            return
            
        email = emails[0]
        content = f"De: {email['from']}\nAssunto: {email['subject']}\nCorpo:\n{email['body'][:3000]}" 

        # Detecta automaticamente se o e-mail é uma Newsletter/Informativo
        is_newsletter = "unsubscribe" in email['body'].lower() or "descadastrar" in email['body'].lower() or "newsletter" in email['from'].lower()

        if is_newsletter:
            system_prompt = """Você é o Nexus, um curador de conteúdo brilhante.
O usuário pediu o resumo detalhado desta Newsletter.

DIRETRIZES DE DEEP DIVE (NEWSLETTER):
- Ignore propagandas, introduções longas ou links de patrocinadores.
- Extraia cada notícia/tópico principal e crie um resumo informativo e bem detalhado.
- NÃO crie 'Próximos Passos', 'Análise de Sentimento' ou 'Sugestão de Resposta'. Este é um e-mail informativo, não um e-mail de trabalho.
- Estruture a saída em blocos bem organizados, usando emojis para ilustrar os temas.

Exemplo de formato:
📰 **[Tópico/Manchete 1]**
(Parágrafo curto explicando a notícia de forma profunda)

🚀 **[Tópico/Manchete 2]**
(Parágrafo curto explicando a notícia de forma profunda)"""
        else:
            system_prompt = """Você é o Nexus. Faça um resumo PROFUNDO e INFORMATIVO.
Estrutura:
📌 **CONTEXTO**: O que está acontecendo?
🧠 **ANÁLISE**: Por que isso é importante? Detalhe os pontos técnicos ou fatos.
⚡ **PRÓXIMOS PASSOS**: O que o usuário deve fazer?
🛡️ **BURNOUT SHIELD**: Faça uma análise de sentimento do e-mail. Se o remetente foi agressivo, passivo-agressivo, ou está fazendo cobranças pesadas fora de hora, crie um alerta aqui. Se o tom for neutro ou amigável, diga: "O tom da mensagem é neutro/amigável".
📝 **SUGESTÃO DE RESPOSTA**: Texto pronto para enviar.

Seja técnico e direto. Use negrito."""

        response = self.llm.analyze(system_prompt, content)
        
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🧹 Marcar como Lido", "callback_data": f"mark_read_{email['id']}"},
                    {"text": "✍️ Criar Rascunho (Reply)", "callback_data": f"draft_{email['id']}"}
                ]
            ]
        }
        
        self.telegram.send_message(chat_id, f"📦 **DETALHES DO E-MAIL**\n\n{response}", reply_markup=reply_markup)
        
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

    def reply_to_email(self, search_query: str, instruction: str, chat_id: int = None, mark_read: bool = False):
        print(f"{Fore.YELLOW}[*] Nexus Engine: Reply Protocol iniciado para query [{search_query}]...{Style.RESET_ALL}")
        self._broadcast(f"✍️ *Preparando rascunho de resposta para:* `{search_query}`...", chat_id)
        
        final_query = search_query if "is:unread" in search_query else f"is:unread {search_query}"
        emails = self.gmail.fetch_emails(query=final_query, limit=1)
        
        if not emails:
            self._broadcast(f"⚠️ Não encontrei o e-mail para responder com a busca `{search_query}`.", chat_id)
            return
            
        email = emails[0]
        content = f"De: {email['from']}\nAssunto: {email['subject']}\nCorpo:\n{email['body'][:2000]}" 

        system_prompt = f"""Você é o 'Nexus', assistente executivo técnico.
O usuário quer responder ao e-mail abaixo.
A instrução do usuário sobre o que responder é: "{instruction}"

Escreva APENAS o corpo do e-mail de resposta. Seja profissional, conciso e use a intenção do usuário.
Não inclua "Assunto:" ou "De:", escreva apenas o texto da mensagem que será enviada."""

        reply_text = self.llm.analyze(system_prompt, content)
        
        draft_id = self.gmail.create_draft(email, reply_text)
        
        if draft_id:
            self._broadcast(f"✅ **RASCUNHO CRIADO NO GMAIL!**\n\n**Para:** {email['from']}\n\n**Mensagem gerada:**\n{reply_text}", chat_id)
        else:
            self._broadcast("❌ Falha ao criar o rascunho no Gmail.", chat_id)
            
        if mark_read:
            self.gmail.mark_as_read([email['id']])
            self._broadcast(f"🧹 *Email de '{email['from']}' marcado como lido.*", chat_id)

    def sync_memory(self, chat_id: int = None):
        """Baixa os últimos e-mails e os injeta no banco vetorial ChromaDB."""
        print(f"{Fore.YELLOW}[*] Nexus Engine: Memory Sync iniciado...{Style.RESET_ALL}")
        self._broadcast("🧠 *Sincronizando 50 e-mails recentes com o banco vetorial local (Isso pode levar alguns minutos)...*", chat_id)
        
        # Puxa 50 emails recentes independente de lido/não lido para ter contexto histórico
        emails = self.gmail.fetch_emails(query='', limit=50)
        if not emails:
            self._broadcast("⚠️ Não encontrei e-mails para sincronizar.", chat_id)
            return
            
        ingested_count = self.memory.ingest_emails(emails)
        self._broadcast(f"✅ **MEMÓRIA ATUALIZADA:** {ingested_count} e-mails foram vetorizados e salvos no banco local.", chat_id)

    def ask_memory(self, question: str, chat_id: int = None):
        """Busca contexto no ChromaDB e usa o LLM para responder à pergunta."""
        print(f"{Fore.YELLOW}[*] Nexus Engine: RAG Memory Query [{question}]...{Style.RESET_ALL}")
        self._broadcast(f"📚 *Buscando memórias passadas sobre:* `{question}`...", chat_id)
        
        context = self.memory.search(question, n_results=5)
        
        if not context:
            self._broadcast("⚠️ Minha memória está vazia ou não encontrei nada relevante. Peça para eu 'sincronizar a memória' primeiro.", chat_id)
            return

        system_prompt = f"""Você é o 'Nexus', assistente executivo técnico.
Responda à pergunta do usuário BASEANDO-SE EXCLUSIVAMENTE nos e-mails abaixo.

CONTEXTO (Memória Vetorial):
{context}

Se a resposta não estiver no contexto, diga claramente que não encontrou informações sobre isso nos e-mails salvos."""

        response = self.llm.analyze(system_prompt, question)
        self._broadcast(f"**🧠 NEXUS RECALL:**\n\n{response}", chat_id)
