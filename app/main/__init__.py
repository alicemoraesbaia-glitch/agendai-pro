from flask import Blueprint

main_bp = Blueprint('main', __name__)

# Importa as rotas para registrá-las no blueprint
from app.main import routes_public, routes_booking, routes_profile, errors