from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='templates')

# Importa as rotas para registrá-las no blueprint
from app.admin import routes_main, routes_users, routes_resources, routes_appointments