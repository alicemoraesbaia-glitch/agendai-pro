from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return "<h1>Smart Agenda: Home</h1><p>Em breve: Lista de Serviços</p>"