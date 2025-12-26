import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, migrate, mail, csrf
from app.models import User 

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static') 
    app.config.from_object(config_class)

    # Inicialização das Extensões
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

    # Registro de Blueprints (Importação local para evitar import circular)
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp # Verifique se admin_bp está definido em app/admin/routes.py
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    
    # Aqui definimos o prefixo apenas UMA vez
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # CLI commands
    from app.cli import register_commands
    register_commands(app)

    return app