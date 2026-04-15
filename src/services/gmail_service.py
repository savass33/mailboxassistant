import os
import html
import base64
import threading
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.config import Config
from colorama import Fore

class GmailService:
    def __init__(self):
        self._lock = threading.Lock()
        self._service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(Config.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(Config.TOKEN_FILE, Config.GMAIL_SCOPES)
        if not creds or not creds.valid:
            print(f"{Fore.YELLOW}⚠️ Credenciais expiradas ou inexistentes. Iniciando fluxo de autorização OAUTH2...{Fore.RESET}")
            flow = InstalledAppFlow.from_client_secrets_file(Config.CREDENTIALS_FILE, Config.GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
            with open(Config.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        return build('gmail', 'v1', credentials=creds)

    def fetch_emails(self, query: str = 'is:unread', limit: int = 10) -> List[Dict]:
        """Busca emails no Gmail utilizando uma string de query."""
        try:
            with self._lock:
                results = self._service.users().messages().list(userId='me', q=query, maxResults=limit).execute()
            messages = results.get('messages', [])
            
            email_data = []
            for msg in messages:
                email_info = self.get_email_details(msg['id'])
                if email_info:
                    email_data.append(email_info)
            return email_data
        except HttpError as error:
            print(f"{Fore.RED}❌ Erro na API do Gmail (Falha de Requisição): {error}{Fore.RESET}")
            return []

    def mark_as_read(self, message_ids: List[str]):
        """Remove a label UNREAD dos emails especificados."""
        try:
            for msg_id in message_ids:
                with self._lock:
                    self._service.users().messages().modify(
                        userId='me', 
                        id=msg_id, 
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao marcar emails como lidos: {e}{Fore.RESET}")

    def get_email_details(self, message_id: str) -> Optional[Dict]:
        """Busca detalhes e desmembra o conteúdo de um email específico."""
        try:
            with self._lock:
                detail = self._service.users().messages().get(userId='me', id=message_id, format='full').execute()
            payload = detail.get('payload', {})
            
            body = self._extract_body(payload)
            snippet = html.escape(detail.get('snippet', ''))
            
            return {
                'id': message_id,
                'threadId': detail.get('threadId', ''),
                'message_id_header': self._get_header(payload, 'Message-ID'),
                'snippet': snippet,
                'from': self._get_header(payload, 'From'),
                'subject': self._get_header(payload, 'Subject'),
                'body': body
            }
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao decodificar dados do email {message_id}: {e}{Fore.RESET}")
            return None

    def create_draft(self, original_email: Dict, reply_text: str) -> Optional[str]:
        """Cria um rascunho de resposta no Gmail mantendo a Thread original."""
        from email.message import EmailMessage
        import base64
        
        try:
            message = EmailMessage()
            message.set_content(reply_text)
            
            # Extrai apenas o email limpo de "Nome <email@dominio.com>"
            import re
            to_email = original_email['from']
            email_match = re.search(r'<([^>]+)>', to_email)
            if email_match:
                to_email = email_match.group(1)
                
            message['To'] = to_email
            
            subject = original_email['subject']
            if not subject.lower().startswith('re:'):
                subject = 'Re: ' + subject
            message['Subject'] = subject
            
            if original_email.get('message_id_header') and original_email['message_id_header'] != "Desconhecido":
                message['In-Reply-To'] = original_email['message_id_header']
                message['References'] = original_email['message_id_header']
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'message': {'raw': encoded_message}}
            
            if original_email.get('threadId'):
                create_message['message']['threadId'] = original_email['threadId']
                
            with self._lock:
                draft = self._service.users().drafts().create(userId='me', body=create_message).execute()
            return draft['id']
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao criar rascunho no Gmail: {e}{Fore.RESET}")
            return None

    def _get_header(self, payload: Dict, name: str) -> str:
        headers = payload.get('headers', [])
        for h in headers:
            if h['name'].lower() == name.lower():
                return html.escape(h['value'])
        return "Desconhecido"

    def _extract_body(self, payload: Dict) -> str:
        """Processa MIME types para extrair o texto plano do corpo do e-mail de forma robusta."""
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif payload.get('mimeType') == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        except Exception:
            pass # Silenciamos falhas de parse MIME para não quebrar a listagem principal
        return ""
