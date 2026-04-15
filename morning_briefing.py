import sys
from colorama import init, Fore
from src.config import Config
from src.core.nexus_agent import NexusAgent

init(autoreset=True)

def run_morning_briefing():
    print(f"{Fore.CYAN}🌅 Iniciando Modo Bom Dia (Morning Briefing)...{Fore.RESET}")
    
    if not Config.TELEGRAM_CHAT_ID:
        print(f"{Fore.RED}❌ Erro: TELEGRAM_CHAT_ID não está configurado no .env! O script não sabe para quem enviar.{Fore.RESET}")
        sys.exit(1)
        
    chat_id = Config.TELEGRAM_CHAT_ID
    nexus = NexusAgent()
    
    # Busca até 15 emails não lidos recentes (ex: da madrugada)
    emails = nexus.gmail.fetch_emails(query='is:unread', limit=15)
    
    if not emails:
        nexus.telegram.send_message(chat_id, "🌅 **BOM DIA, SAVAS!**\n\nSua caixa de entrada está limpa. Nenhuma novidade na madrugada. Excelente dia de trabalho! ☕")
        print(f"{Fore.GREEN}✅ Briefing enviado: Caixa limpa.{Fore.RESET}")
        return

    email_text = "\n".join([f"De: {e['from']} | Assunto: {e['subject']} | Snippet: {e['snippet']}" for e in emails])
    
    system_prompt = """Você é o 'Nexus', assistente executivo técnico de alta performance.
Crie um Briefing Matinal (Morning Briefing) para o usuário Savas ao acordar.

DIRETRIZES:
- Inicie com um "Bom dia, Savas! 🌅 Aqui está o seu briefing tático de hoje."
- Analise os e-mails abaixo e agrupe as informações em 3 blocos:
  1. 🔥 URGENTE / PARA HOJE (Foque em prazos, chefia, emprego).
  2. 💰 FINANCEIRO (Gastos, recibos, banco).
  3. 📰 RADAR (Notícias, artigos interessantes).
- Ignore spam e e-mails irrelevantes.
- Seja enérgico, direto e encorajador.

E-MAILS DA MADRUGADA:"""

    try:
        response = nexus.llm.analyze(system_prompt, email_text)
        nexus.telegram.send_message(chat_id, response)
        print(f"{Fore.GREEN}✅ Morning Briefing gerado e despachado com sucesso!{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao gerar o briefing: {e}{Fore.RESET}")

if __name__ == "__main__":
    run_morning_briefing()