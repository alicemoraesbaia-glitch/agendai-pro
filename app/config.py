import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

class Config:
    # --- Chave de Segurança ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    
    # --- Banco de Dados ---
    # Garante que o SQLAlchemy não use 'postgres://' (antigo) em vez de 'postgresql://' se mudar de banco
    uri = os.environ.get('DATABASE_URL') or 'sqlite:///smart_agenda.db'
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- Localização ---
    TIMEZONE = os.environ.get('TIMEZONE') or 'America/Sao_Paulo'
    
    # --- Configurações de Email (SMTP) ---
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    
    # Converte 'true' do .env para o booleano True do Python
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Importante: O Gmail exige que o SENDER seja o próprio e-mail da conta
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    MAIL_DEBUG = True  # Adicione esta linha

    # --- Segurança de Sessão ---
    # Mudança: Usamos FLASK_DEBUG para facilitar o desenvolvimento local
    DEBUG = os.environ.get('FLASK_DEBUG') == '1'
    
    # Se estiver em DEBUG (desenvolvimento), não exige HTTPS. Se estiver em produção, exige.
    SESSION_COOKIE_SECURE = not DEBUG
    REMEMBER_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True