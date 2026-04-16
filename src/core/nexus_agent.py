import json
import re
from colorama import Fore, Style
from src.services.gmail_service import GmailService
from src.services.llm_service import LLMService
from src.services.telegram_service import TelegramService
from src.services.memory_service import MemoryService
from src.services.calendar_service import CalendarService

class NexusAgent:
    def __init__(self):
        self.gmail = GmailService()
        self.llm = LLMService()
        self.telegram = TelegramService()
        self.memory = MemoryService()
        self.calendar = CalendarService()

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
        
        router_prompt = f"""Você é um parser JSON. Sua única tarefa é analisar a entrada e cuspir UM JSON válido.
Você DEVE escolher UMA destas 'actions' permitidas:
"triage" = Resumir a caixa de entrada, ver não lidos de forma geral ou marcar lidos.
"deepdive" = Ler um e-mail de um remetente ESPECÍFICO ou perguntar sobre um assunto específico (ex: "do chefe", "sobre o portfólio", "do que se trata essa etapa").
"news" = Ler apenas newsletters ou notícias.
"reply" = Responder a um e-mail.
"schedule" = Agendar um e-mail.
"delete" = Apagar ou excluir um e-mail específico.
"sync_memory" = Salvar e-mails na memória vetorial.
"ask_memory" = Responder perguntas sobre histórico antigo.
"chat" = Conversa genérica, tirar dúvidas, ou falar com o assistente.

Regras CRÍTICAS:
- Se o usuário perguntar "do que se trata X" ou "me dê mais detalhes sobre Y", a action é SEMPRE "deepdive".
- "mark_read" deve ser FALSE por padrão. Mude para TRUE APENAS SE o usuário disser explicitamente as palavras "limpar", "marcar como lido" ou "apagar notificação".
- Se a action for "deepdive", "delete" ou "reply", defina a "query" usando operadores GMAIL se possível (ex: "from:filipe", "subject:portfólio", "from:gupy"). Se não houver remetente claro, use termos chave.
- NUNCA invente actions.

Entrada do usuário: "{user_text}"
"""
        
        try:
            print(f"{Fore.YELLOW}[*] Nexus Engine: Roteando intenção via LLM...{Style.RESET_ALL}")
            intent_response = self.llm.analyze("Responda APENAS com um objeto JSON válido.", router_prompt)
            print(f"DEBUG LLM Router: {intent_response}")
            
            match = re.search(r'\{.*?\}', intent_response, re.DOTALL)
            if not match: raise ValueError("JSON não encontrado.")
            intent = json.loads(match.group(0).strip())
            
            action = intent.get("action", "chat")
            
            # Força o fallback se a IA inventar uma action inválida
            allowed_actions = ["triage", "deepdive", "news", "reply", "schedule", "delete", "sync_memory", "ask_memory", "chat"]
            if action not in allowed_actions:
                action = "triage" if intent.get("mark_read") else "chat"
                
            query = intent.get("query", "")
            instruction = intent.get("instruction", "")
            if action not in ["deepdive", "reply", "delete", "ask_memory", "schedule"]: query = ""
            
            # Trata o mark_read para garantir que seja Booleano
            mark_read_val = intent.get("mark_read", False)
            mark_read = str(mark_read_val).lower() == "true"
            
            print(f"{Fore.GREEN}[+] Intenção: {action} | Query: {query} | Instruction: {instruction} | MarkRead: {mark_read}{Style.RESET_ALL}")

            if action == "triage":
                self.triage_unread(chat_id, mark_read)
            elif action == "news":
                self.process_newsletters(chat_id, mark_read)
            elif action == "deepdive":
                self.deep_dive(query, chat_id, mark_read, original_text=user_text)
            elif action == "reply":
                self.reply_to_email(query, instruction, chat_id, mark_read)
            elif action == "schedule":
                self.schedule_event(query, chat_id, mark_read)
            elif action == "delete":
                self.prepare_deletion(query, chat_id)
            elif action == "sync_memory":
                self.sync_memory(chat_id)
            elif action == "ask_memory":
                self.ask_memory(query, chat_id)
            elif action == "chat":
                # Processa perguntas genéricas usando o contexto histórico do LLM
                response = self.llm.analyze("Você é o Nexus, assistente de e-mail. Responda de forma direta e técnica.", user_text)
                self._broadcast(f"🤖 **NEXUS:**\n{response}", chat_id)
            else:
                self._broadcast("🤖 **NEXUS:** Comando não reconhecido.", chat_id)
                
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
        
        system_prompt = """Você é um assistente executivo focado e infalível.
Sua ÚNICA função é classificar os emails fornecidos e gerar uma lista formatada.
Você NÃO PODE cometer erros. Você DEVE seguir a lógica exata abaixo:

🔴 | CRÍTICO | E-mails sobre: Emprego, Vagas, Gupy, Admissão, Documentos, Estágio, Portfólio, Segurança, Prazos urgentes.
🔵 | FINANCEIRO | E-mails sobre: Bancos, Nubank, Inter, Pix, Gastos, Faturas.
🟢 | NOTÍCIAS | E-mails sobre: Newsletters (Filipe Deschamps), Artigos, Resumos semanais.
⚪ | NOISE | E-mails sobre: Pesquisa de satisfação (Bluefit, opiniões), Promoções (Steam, jogos), Spam, Lembretes genéricos.

FORMATO OBRIGATÓRIO POR EMAIL (EXATAMENTE UMA LINHA COM PIPES):
TAG | CATEGORIA | Nome do Remetente - Assunto. (Resumo em 1 frase).

EXEMPLOS DE CLASSIFICAÇÃO PERFEITA (Siga este padrão para os emails reais):
🔴 | CRÍTICO | Gupy - Você tem documentos pendentes para concluir a sua admissão. (Processo seletivo exige envio de documentos).
🔴 | CRÍTICO | Aline - Etapa Portfólio Pessoal. (Confirmação de envio de portfólio para estágio).
⚪ | NOISE | Bluefit - Queremos saber a sua opiniao! (Pesquisa de satisfação de academia).
⚪ | NOISE | Steam - Squad from your Steam wishlist is now on sale! (Promoção de jogo).
🟢 | NOTÍCIAS | Filipe Deschamps - Lei contra impressoras 3D. (Resumo de notícias diárias).

Você será penalizado se classificar um e-mail de admissão (Gupy) como NOISE ou uma pesquisa de opinião (Bluefit) como CRÍTICO. Preste atenção aos remetentes e assuntos!"""

        try:
            response = self.llm.analyze("Gere APENAS as linhas no formato 'TAG | CATEGORIA | Texto'. Para cada email fornecido abaixo, crie UMA linha correspondente.", system_prompt + "\n\nEMAILS REAIS A PROCESSAR:\n" + email_text)
            print(f"DEBUG LLM Triage:\n{response}")
            
            lines = [l.strip() for l in response.strip().split('\n') if '|' in l and len(l.split('|')) >= 3]
            
            if not lines:
                # Fallback seguro caso a IA não use o pipe (|)
                lines = [f"⚪ | NOISE | {e['from']} - {e['subject']}" for e in emails]

            self._broadcast("<b>📋 RELATÓRIO DE TRIAGEM ATUALIZADO</b>", chat_id)
            
            # Divide as linhas em bubbles de 3
            for i in range(0, len(lines), 3):
                chunk = lines[i:i+3]
                bubble = ""
                for line in chunk:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        tag = parts[0].strip()
                        # Se a IA esquecer o emoji, forçamos um padrão para não quebrar o layout
                        if tag not in ["🔴", "🔵", "🟢", "⚪"]:
                            if "CRÍTICO" in parts[1].upper(): tag = "🔴"
                            elif "FINANCEIRO" in parts[1].upper(): tag = "🔵"
                            elif "NOTÍCIAS" in parts[1].upper(): tag = "🟢"
                            else: tag = "⚪"
                            
                        cat = parts[1].strip()
                        content = "|".join(parts[2:]).strip()
                        bubble += f"{tag} <b>{cat}</b>\n{content}\n\n"
                
                if bubble:
                    self.telegram.send_message(chat_id, bubble)

            if mark_read:
                print(f"{Fore.MAGENTA}[*] Gmail: Marcando {len(emails)} emails como lidos...{Fore.RESET}")
                self.gmail.mark_as_read([e['id'] for e in emails])
                self._broadcast("🧹 *Limpeza concluída: Emails marcados como lidos.*", chat_id)

        except Exception as e:
            self._broadcast(f"❌ Falha no processamento: {e}", chat_id)

    def deep_dive(self, search_query: str, chat_id: int = None, mark_read: bool = False, original_text: str = ""):
        print(f"{Fore.YELLOW}[*] Nexus Engine: Deep Dive em {search_query}...{Style.RESET_ALL}")
        self._broadcast(f"🕵️‍♂️ *Infiltrando e-mails: `{search_query}`...*", chat_id)

        # Aumentamos o limite para permitir que o LLM escolha o melhor e-mail
        emails = self.gmail.fetch_emails(query=search_query, limit=5)
        
        if not emails:
            self._broadcast(f"⚠️ Nenhum e-mail localizado para a busca `{search_query}`.", chat_id)
            return

        # Se houver mais de um e-mail, pedimos ao LLM para selecionar o mais relevante
        if len(emails) > 1 and original_text:
            print(f"{Fore.YELLOW}[*] Nexus Engine: Selecionando e-mail mais relevante entre {len(emails)} resultados...{Style.RESET_ALL}")
            selection_prompt = f"""O usuário pediu: "{original_text}"
A busca retornou os seguintes e-mails:
"""
            for i, e in enumerate(emails):
                selection_prompt += f"[{i}] De: {e['from']} | Assunto: {e['subject']} | Snippet: {e['snippet']}\n"

            selection_prompt += "\nResponda APENAS com o número do índice (ex: 0, 1, 2) do e-mail que melhor corresponde ao pedido. Se nenhum for relevante, responda 'none'."

            try:
                choice_raw = self.llm.analyze("Responda apenas com o número ou 'none'.", selection_prompt).strip()
                if choice_raw.isdigit() and int(choice_raw) < len(emails):
                    email = emails[int(choice_raw)]
                else:
                    email = emails[0] # Fallback para o mais recente
            except:
                email = emails[0]
        else:
            email = emails[0]

        content = f"De: {email['from']}\nAssunto: {email['subject']}\nCorpo:\n{email['body'][:4000]}"

        # Detecta automaticamente se o e-mail é uma Newsletter/Informativo
        body_lower = email['body'].lower()
        newsletter_keywords = ["unsubscribe", "descadastrar", "newsletter", "clique aqui", "view in browser", "mailing list", "preferências", "visualizar no navegador"]
        is_newsletter = any(kw in body_lower for kw in newsletter_keywords) or "newsletter" in email['from'].lower() or "newsletter" in email['subject'].lower()

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

    def schedule_event(self, search_query: str, chat_id: int = None, mark_read: bool = False):
        """Lê um e-mail, extrai dados de agendamento e cria no Google Calendar."""
        print(f"{Fore.YELLOW}[*] Nexus Engine: Schedule Protocol iniciado para query [{search_query}]...{Style.RESET_ALL}")
        self._broadcast(f"📅 *Analisando e-mail para agendamento:* `{search_query}`...", chat_id)
        
        final_query = search_query if "is:unread" in search_query else f"is:unread {search_query}"
        emails = self.gmail.fetch_emails(query=final_query, limit=1)
        
        if not emails:
            self._broadcast(f"⚠️ Não encontrei o e-mail para agendar com a busca `{search_query}`.", chat_id)
            return
            
        email = emails[0]
        content = f"De: {email['from']}\nAssunto: {email['subject']}\nCorpo:\n{email['body'][:2000]}" 

        import datetime
        now = datetime.datetime.now().isoformat()
        
        system_prompt = f"""Você é o 'Nexus', assistente executivo.
Extraia os dados de agendamento (reunião, entrevista, prazo) do e-mail fornecido.
A data/hora atual é: {now}.

Retorne APENAS um JSON com os campos:
- title: Título curto do evento.
- description: Resumo do que é.
- start_iso: Data e hora de início no formato ISO 8601 (ex: "2026-04-20T14:00:00-03:00"). ESTIME com base no texto e na data atual.

EXEMPLO DE RESPOSTA:
{{"title": "Entrevista Gupy", "description": "Entrevista técnica com o RH", "start_iso": "2026-04-20T14:00:00-03:00"}}"""

        try:
            response = self.llm.analyze("Responda APENAS JSON puro.", system_prompt + "\n\nEMAIL:\n" + content)
            
            match = re.search(r'\{.*?\}', response, re.DOTALL)
            if not match: raise ValueError("JSON não encontrado na resposta.")
            event_data = json.loads(match.group(0).strip())
            
            link = self.calendar.create_event(
                summary=event_data.get('title', 'Evento Nexus'),
                description=event_data.get('description', 'Criado automaticamente pelo Nexus Agent'),
                start_time_iso=event_data.get('start_iso')
            )
            
            if link:
                self._broadcast(f"✅ **EVENTO AGENDADO COM SUCESSO!**\n\n**Título:** {event_data.get('title')}\n**Data:** {event_data.get('start_iso')}\n\n🔗 [Link para o Calendar]({link})", chat_id)
            else:
                self._broadcast("❌ Falha ao criar o evento no Google Calendar.", chat_id)
                
            if mark_read:
                self.gmail.mark_as_read([email['id']])
                
        except Exception as e:
            self._broadcast(f"❌ Erro ao extrair dados de agendamento: {e}", chat_id)

    def prepare_deletion(self, search_query: str, chat_id: int):
        """Prepara um e-mail para exclusão, exigindo confirmação do usuário."""
        print(f"{Fore.RED}[*] Nexus Engine: Deletion Protocol iniciado para query [{search_query}]...{Style.RESET_ALL}")
        self._broadcast(f"⚠️ *Buscando e-mail para exclusão:* `{search_query}`...", chat_id)
        
        emails = self.gmail.fetch_emails(query=search_query, limit=1)
        
        if not emails:
            self._broadcast(f"⚠️ Não encontrei nenhum e-mail correspondente a `{search_query}` para apagar.", chat_id)
            return
            
        email = emails[0]
        
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🚨 CONFIRMAR EXCLUSÃO", "callback_data": f"delete_{email['id']}"},
                    {"text": "❌ CANCELAR", "callback_data": "cancel_delete"}
                ]
            ]
        }
        
        warning_msg = f"🛑 **ATENÇÃO: CONFIRMAÇÃO DE EXCLUSÃO** 🛑\n\nVocê solicitou apagar o seguinte e-mail:\n\n**De:** {email['from']}\n**Assunto:** {email['subject']}\n\nTem certeza absoluta? Esta ação moverá o e-mail para a Lixeira."
        self.telegram.send_message(chat_id, warning_msg, reply_markup=reply_markup)
