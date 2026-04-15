from src.config import Config
from colorama import Fore

class DBService:
    def __init__(self):
        self.conn = None
        print(f"{Fore.YELLOW}[DB WARNING] PostgreSQL temporariamente desativado para testes de IA.{Fore.RESET}")

    def execute_query(self, query: str, params: tuple = ()):
        return None
