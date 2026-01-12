import logging
from flask import render_template
from app.main import main_bp
from app.extensions import db

# Configuração de Log Simples (Sênior: permite rastrear o erro no console/arquivo)
logger = logging.getLogger(__name__)

@main_bp.app_errorhandler(403)
def forbidden_error(error):
    """Erro de acesso negado (ex: usuário comum tentando entrar no admin)"""
    return render_template('errors/403.html'), 403

@main_bp.app_errorhandler(404)
def not_found_error(error):
    """Página não encontrada"""
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    """Erro interno do servidor"""
    # 1. ROLLBACK: Se o erro foi no banco, desfaz a transação pendente para evitar sujeira
    db.session.rollback()
    
    # 2. LOG: Registra o erro exato para o desenvolvedor ver no terminal/log
    logger.error(f"Erro Interno 500: {str(error)}")
    
    return render_template('errors/500.html'), 500