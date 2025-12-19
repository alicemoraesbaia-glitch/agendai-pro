from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    return "Página de Login (Em breve)"

@auth_bp.route('/register')
def register():
    return "Página de Registro (Em breve)"