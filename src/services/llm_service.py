from openai import OpenAI
from src.config import Config
from colorama import Fore

class LLMService:
    def __init__(self):
        self.client = OpenAI(base_url=Config.OLLAMA_URL, api_key="ollama")

    def analyze(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3 # Baixa temperatura para foco executivo e analítico
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"{Fore.RED}❌ Falha Crítica no Motor de IA (Ollama): {e}{Fore.RESET}")
            return "Erro: Motor de IA inacessível."
