# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Smart Agenda (Agendai Pro)
# Copyright (c) 2026 Eralice de Moraes Baía. Todos os direitos reservados.
# 
# Este código é PROPRIETÁRIO e CONFIDENCIAL. A reprodução, 
# distribuição ou modificação não autorizada é estritamente proibida.
# Desenvolvido para fins acadêmicos - Curso de Engenharia de Software UNINTER.
# Acadêmica: Eralice de Moraes Baía | RU: 4144099
# --------------------------------------------------------------------------
import os
from flask import Flask
from app.config import config_dict 
from app.extensions import db, login_manager, migrate, mail, csrf
from app.models import User 

def create_app(config_name='development'):
    app = Flask(__name__, static_folder='static') 
    
    # Busca a classe de configuração. Se não achar, usa 'development'
    config_class = config_dict.get(config_name, config_dict['development'])
    app.config.from_object(config_class)

    # Inicialização das Extensões
    db.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Acesso restrito. Por favor, faça login."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # AJUSTE SÊNIOR: render_as_batch só é True se o banco for SQLite
    # Isso evita conflitos em bancos profissionais como PostgreSQL
    is_sqlite = app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite:')
    migrate.init_app(app, db, render_as_batch=is_sqlite)
    
    mail.init_app(app)
    csrf.init_app(app)

    # Blueprints e CLI
    from app.auth.routes import auth_bp
    from app.main import main_bp
    from app.admin import admin_bp 
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.cli import register_commands
    register_commands(app)

    return app