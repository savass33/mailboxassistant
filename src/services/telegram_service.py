import requests
from src.config import Config
from colorama import Fore

class TelegramService:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}"

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML", reply_markup: dict = None) -> bool:
        if not text:
            return False
            
        url = f"{self.base_url}/sendMessage"
        
        safe_text = text.replace("**", "<b>").replace("</b><b>", "")

        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            response = requests.post(url, json={**payload, "parse_mode": "HTML"}, timeout=10)
            if response.status_code != 200:
                print(f"{Fore.YELLOW}⚠️ Erro de HTML no Telegram. Enviando em texto puro...{Fore.RESET}")
                requests.post(url, json=payload, timeout=10)
                
            print(f"{Fore.GREEN}✅ Mensagem despachada para o Telegram!{Fore.RESET}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Erro crítico de rede ao contactar Telegram: {e}{Fore.RESET}")
            return False

    def delete_webhook(self):
        """Deleta o Webhook para permitir o modo Polling (escuta ativa)."""
        url = f"{self.base_url}/deleteWebhook"
        try:
            requests.get(url, timeout=10)
        except Exception:
            pass

    def get_updates(self, offset=None, timeout=60) -> list:
        """Busca novas mensagens ativamente no Telegram via Long Polling."""
        url = f"{self.base_url}/getUpdates"
        params = {'timeout': timeout, 'allowed_updates': ['message']}
        if offset:
            params['offset'] = offset
            
        try:
            response = requests.get(url, params=params, timeout=timeout + 10)
            if response.status_code == 200:
                return response.json().get('result', [])
            return []
        except requests.exceptions.ReadTimeout:
            # Timeout normal de Long Polling, apenas ignora
            return []
        except Exception as e:
            print(f"{Fore.RED}⚠️ Aviso de Rede (Ignorável): Falha ao buscar no Telegram. Tentando novamente em breve...{Fore.RESET}")
            return []
