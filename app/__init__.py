import os
from flask import Flask
# Importamos o dicionário de configurações em vez da classe única
from app.config import config_dict 
from app.extensions import db, login_manager, migrate, mail, csrf
from app.models import User 

def create_app(config_name='development'):
    """
    Application Factory: Inicializa o app com base no ambiente selecionado.
    Valores possíveis para config_name: 'development', 'testing', 'production'
    """
    app = Flask(__name__, static_folder='static') 
    
    # Busca a classe de configuração correta dentro do dicionário
    # Se o nome não existir, o .get() usa a configuração de 'development' por padrão
    config_class = config_dict.get(config_name, config_dict['development'])
    app.config.from_object(config_class)

    # Inicialização das Extensões - Agora com a URI do banco carregada corretamente
    db.init_app(app)
    
    # CONFIGURAÇÃO DO LOGIN MANAGER
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Acesso restrito. Por favor, faça login."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    migrate.init_app(app, db, render_as_batch=True)
    mail.init_app(app)
    csrf.init_app(app)

    # Registro de Blueprints
    from app.auth.routes import auth_bp
    from app.main import main_bp
    from app.admin import admin_bp 
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # CLI commands
    from app.cli import register_commands
    register_commands(app)

    return app