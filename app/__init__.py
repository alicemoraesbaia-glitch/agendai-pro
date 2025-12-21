import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, migrate, mail, csrf
from app.models import User # Importe o modelo User para o loader

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicialização das Extensões
    db.init_app(app)
    
    # --- CONFIGURAÇÃO DO LOGIN MANAGER ---
    login_manager.init_app(app)
    
    # Define a rota de redirecionamento quando o acesso for negado
    # 'auth.login' refere-se à Blueprint 'auth' e à função 'login'
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Acesso restrito. Por favor, faça login."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        # Converte o ID da sessão para o objeto User do banco
        return User.query.get(int(user_id))
    # --------------------------------------
    
    # IMPORTANTE: render_as_batch=True permite migrações no SQLite
    migrate.init_app(app, db, render_as_batch=True)
    
    mail.init_app(app)
    csrf.init_app(app)

    # Registro de Blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # CLI commands
    from app.cli import register_commands
    register_commands(app)

    return app