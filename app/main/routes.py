from flask import render_template
from app.main import main_bp
from app.models import Service

@main_bp.route('/')
def index():
    # Buscamos os serviços ativos para exibir na landing page
    services = Service.query.filter_by(active=True).all()
    return render_template('main/index.html', services=services)