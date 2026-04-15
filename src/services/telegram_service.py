import requests
from src.config import Config
from colorama import Fore

class TelegramService:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}"

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
        if not text:
            return False
            
        url = f"{self.base_url}/sendMessage"
        
        # Tratamento rápido de formatação (o modelo usa negrito em markdown **texto**, 
        # mas convertemos aspas duplas de markdown pro formato <b> se usarmos HTML)
        # O HTML no Telegram é mais seguro e evita crashes com caracteres isolados.
        safe_text = text.replace("**", "<b>").replace("</b><b>", "")
        # Como replace simples pode abrir <b> e não fechar, vamos usar parse_mode=None se falhar, ou limpar formatação complexa.
        # Deixarei o parse mode flexivel pro webhook, mas o bot tentará sem parse mode se der erro de formatação.

        payload = {"chat_id": chat_id, "text": text}
        
        try:
            # Tenta mandar com HTML primeiro, se der pau por causa de caracteres sujos do Ollama, manda sem formatação.
            response = requests.post(url, json={**payload, "parse_mode": "HTML"}, timeout=10)
            if response.status_code != 200:
                print(f"{Fore.YELLOW}⚠️ Erro de HTML no Telegram. Enviando em texto puro...{Fore.RESET}")
                requests.post(url, json=payload, timeout=10)
                
            print(f"{Fore.GREEN}✅ Mensagem despachada para o Telegram!{Fore.RESET}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Erro crítico de rede ao contactar Telegram: {e}{Fore.RESET}")
            return False
