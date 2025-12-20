import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, migrate, mail, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)  # <--- Isso ativa o motor de e-mail
    csrf.init_app(app)

    # Register Blueprints
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