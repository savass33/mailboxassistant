import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.config import Config
from colorama import Fore

class CalendarService:
    def __init__(self):
        self._service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(Config.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(Config.TOKEN_FILE, Config.GMAIL_SCOPES)
        if not creds or not creds.valid:
            print(f"{Fore.YELLOW}⚠️ Credenciais do Calendar expiradas ou inexistentes. Autorize no navegador...{Fore.RESET}")
            flow = InstalledAppFlow.from_client_secrets_file(Config.CREDENTIALS_FILE, Config.GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
            with open(Config.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        return build('calendar', 'v3', credentials=creds)

    def create_event(self, summary: str, description: str, start_time_iso: str, end_time_iso: str = None) -> str:
        """Cria um evento no Google Calendar e retorna o link para o evento."""
        try:
            # Se não tiver horário de término, define como 1 hora depois do início
            if not end_time_iso:
                start_dt = datetime.datetime.fromisoformat(start_time_iso.replace('Z', '+00:00'))
                end_dt = start_dt + datetime.timedelta(hours=1)
                end_time_iso = end_dt.isoformat()

            event = {
              'summary': summary,
              'description': description,
              'start': {
                'dateTime': start_time_iso,
                'timeZone': 'America/Sao_Paulo',
              },
              'end': {
                'dateTime': end_time_iso,
                'timeZone': 'America/Sao_Paulo',
              },
              'reminders': {
                'useDefault': False,
                'overrides': [
                  {'method': 'email', 'minutes': 24 * 60},
                  {'method': 'popup', 'minutes': 30},
                ],
              },
            }

            event_result = self._service.events().insert(calendarId='primary', body=event).execute()
            print(f"{Fore.GREEN}[+] Evento criado no Calendar: {event_result.get('htmlLink')}{Fore.RESET}")
            return event_result.get('htmlLink')
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao criar evento no Calendar: {e}{Fore.RESET}")
            return None
