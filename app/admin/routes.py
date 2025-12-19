from flask import Blueprint
from flask_login import login_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return "Painel Administrativo"