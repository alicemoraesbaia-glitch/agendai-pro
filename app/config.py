import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações Base - Comum a todos os ambientes"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.environ.get('TIMEZONE') or 'America/Sao_Paulo'
    
    # Configurações de Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')

class DevelopmentConfig(Config):
    """Configuração para o seu PC (Localhost)"""
    DEBUG = True
    # Usa SQLite local por padrão
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///smart_agenda.db'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

class TestingConfig(Config):
    """Configuração para a Seção 14.3 (Pytest)"""
    TESTING = True
    # Banco em memória para ser rápido e não sujar seu app.db
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Configuração para o Servidor na Nuvem (PostgreSQL)"""
    DEBUG = False
    
    # Lógica sênior para o PostgreSQL
    uri = os.environ.get('DATABASE_URL')
    
    # Se a variável estiver vazia, o sistema deve parar e avisar, 
    # em vez de tentar usar SQLite
    if not uri:
        raise ValueError("ERRO: A variável DATABASE_URL não foi encontrada no Render!")

    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = uri
    
    # Segurança Máxima em Produção
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

# Dicionário para facilitar a seleção no __init__.py ou create_app()
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}