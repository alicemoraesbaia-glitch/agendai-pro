from flask import render_template
from flask_login import login_required, current_user
from app.admin import admin_bp
from flask import abort

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Segurança Sênior: Apenas admins podem ver esta página
    if not current_user.is_admin:
        abort(403) # Erro de Proibido
        
    return render_template('admin/dashboard.html')