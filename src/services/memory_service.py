import os
import chromadb
from chromadb.config import Settings
from colorama import Fore

class MemoryService:
    def __init__(self):
        # Inicializa o banco de dados vetorial local (ChromaDB)
        self.db_path = os.path.join(os.getcwd(), "memory_db")
        os.makedirs(self.db_path, exist_ok=True)
        
        try:
            # O ChromaDB usa um modelo leve de embeddings (all-MiniLM-L6-v2) por padrão 
            # que roda via ONNX na CPU sem precisar da internet.
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(name="email_memory")
            print(f"{Fore.GREEN}[*] Memory Bank (Vector DB) inicializado com sucesso.{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao inicializar o Memory Bank: {e}{Fore.RESET}")
            self.client = None

    def ingest_emails(self, emails: list) -> int:
        """Vetoriza e salva os e-mails no banco de memória."""
        if not self.client or not emails:
            return 0

        documents = []
        metadatas = []
        ids = []

        for e in emails:
            # Formata o documento que será vetorizado
            doc = f"Remetente: {e['from']}\nAssunto: {e['subject']}\nConteúdo: {e['body']}"
            documents.append(doc)
            
            # Salva metadados úteis para filtro ou visualização
            metadatas.append({
                "from": e['from'],
                "subject": e['subject'],
                "message_id": e['id']
            })
            ids.append(e['id'])

        try:
            # Adiciona ou atualiza no banco vetorial
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return len(ids)
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao ingerir e-mails na memória: {e}{Fore.RESET}")
            return 0

    def search(self, query: str, n_results: int = 5) -> str:
        """Busca os e-mails mais relevantes semanticamente."""
        if not self.client:
            return ""

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            context = ""
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i]
                    context += f"--- E-mail {i+1} ---\n{doc}\n\n"
            return context
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na busca vetorial: {e}{Fore.RESET}")
            return ""
