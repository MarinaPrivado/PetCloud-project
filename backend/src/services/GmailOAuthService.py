import os
import json
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Caminho para o arquivo de credenciais OAuth (na pasta src, não services)
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'OAuthID.json')
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailOAuthService:
    def __init__(self):
        self.creds = None
        self.service = None
        
    def get_credentials(self):
        """Obtém ou atualiza as credenciais OAuth"""
        # Verifica se já existe um token salvo
        if os.path.exists(TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # Se não há credenciais válidas, precisa autenticar
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Erro ao renovar token: {e}")
                    return None
            else:
                return None  # Precisa fazer o fluxo OAuth completo
        
        # Salva as credenciais para a próxima execução
        with open(TOKEN_FILE, 'w') as token:
            token.write(self.creds.to_json())
        
        return self.creds
    
    def create_oauth_flow(self, redirect_uri):
        """Cria o fluxo OAuth para autenticação"""
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        return flow
    
    def get_authorization_url(self, redirect_uri):
        """Gera a URL de autorização OAuth"""
        flow = self.create_oauth_flow(redirect_uri)
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url, state
    
    def exchange_code_for_token(self, code, redirect_uri):
        """Troca o código de autorização por um token de acesso"""
        flow = self.create_oauth_flow(redirect_uri)
        flow.fetch_token(code=code)
        self.creds = flow.credentials
        
        # Salva as credenciais
        with open(TOKEN_FILE, 'w') as token:
            token.write(self.creds.to_json())
        
        return self.creds
    
    def send_email(self, to_email, subject, body):
        """Envia um email usando a Gmail API"""
        try:
            # Obtém credenciais
            creds = self.get_credentials()
            if not creds:
                print("[EMAIL] Credenciais OAuth não disponíveis. Execute o fluxo de autorização primeiro.")
                return False
            
            # Cria o serviço Gmail
            service = build('gmail', 'v1', credentials=creds)
            
            # Cria a mensagem
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject
            
            # Codifica a mensagem
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Envia o email
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f'[EMAIL] Email enviado com sucesso! Message Id: {send_message["id"]}')
            return True
            
        except HttpError as error:
            print(f'[EMAIL] Erro HTTP ao enviar email: {error}')
            return False
        except Exception as e:
            print(f'[EMAIL] Erro ao enviar email: {e}')
            return False
    
    def is_authenticated(self):
        """Verifica se o serviço está autenticado"""
        creds = self.get_credentials()
        return creds is not None and creds.valid


# Instância global do serviço
gmail_service = GmailOAuthService()
