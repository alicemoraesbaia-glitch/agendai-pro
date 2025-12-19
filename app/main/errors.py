from flask import render_template
from app.main import main_bp

@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    # Aqui poderíamos enviar um log para o desenvolvedor
    return render_template('errors/500.html'), 500