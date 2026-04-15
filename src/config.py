import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Mensageria (Telegram)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # IA Local (Ollama)
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:3b")

    # Banco de Dados (PostgreSQL)
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

    # Configurações do Gmail
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "cred.json")
    TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")

    # Configurações do App
    DEBUG = os.getenv("DEBUG", "True") == "True"
    PORT = int(os.getenv("PORT", 5000))
