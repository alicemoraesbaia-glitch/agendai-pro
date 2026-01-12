from flask import render_template, request
from app.extensions import db
from app.main import main_bp
from app.models import Service, Resource

# --- ROTA: HOME (INDEX) ---
@main_bp.route('/')
def index():
    # 1. Pegamos os parâmetros da URL
    query_param = request.args.get('q', '')
    category_param = request.args.get('category', '')

    # 2. Categorias para o menu
    categories_raw = db.session.query(Service.category).filter(Service.active==True).distinct().all()
    categories = [c[0] for c in categories_raw]

    # 3. Base da busca de serviços
    services_query = Service.query.filter_by(active=True)

    # 4. Aplicação dos filtros
    if query_param:
        services_query = services_query.filter(Service.name.ilike(f'%{query_param}%'))

    if category_param and category_param != 'Todos':
        services_query = services_query.filter_by(category=category_param)

    # 5. Executa a busca
    services = services_query.all()

    return render_template('main/index.html', 
                           services=services, 
                           categories=categories,
                           active_category=category_param,
                           search_query=query_param)

# --- ROTA: EXPLORAR POR CATEGORIA ---
@main_bp.route('/explorar/<category_name>')
def explore_category(category_name):
    services = Service.query.filter_by(category=category_name, active=True).all()
    return render_template('main/category_explore.html', 
                           category=category_name, 
                           services=services)

# --- ROTA: CATÁLOGO DE SERVIÇOS ---
@main_bp.route('/servicos')
def list_services():
    services = Service.query.filter_by(active=True).order_by(Service.category).all()
    
    categories_query = db.session.query(Service.category).filter_by(active=True).distinct().all()
    categories = sorted([c[0] for c in categories_query])
    
    return render_template('main/services_catalog.html', 
                           services=services, 
                           categories=categories,
                           title="Nossos Procedimentos")

# --- ROTA: DETALHE DO SERVIÇO ---
@main_bp.route('/servico/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    return render_template('main/service_detail.html', service=service)

# --- ROTA: ESPECIALISTAS PÚBLICOS ---
@main_bp.route('/especialistas')
def public_professionals():
    professionals = Resource.query.all()
    return render_template('main/professionals.html', professionals=professionals)