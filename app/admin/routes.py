from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.admin import admin_bp
from app.models import Appointment, Service, User, Resource
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from functools import wraps

# --- DECORADOR DE SEGURANÇA (O PORTEIRO) ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function



@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    from datetime import datetime, timedelta
    now = datetime.now()
    today = now.date()

    # 1. PEGAR TODOS OS AGENDAMENTOS DE HOJE (A lista que sumiu)
    # Importante: usamos func.date para comparar apenas a data, ignorando a hora
    services_today = Appointment.query.filter(
        db.func.date(Appointment.start_datetime) == today,
        Appointment.status != 'cancelled'
    ).order_by(Appointment.start_datetime.asc()).all()

    # 2. PEGAR O FEED GERAL (Para os cards de pendentes)
    all_appointments = Appointment.query.order_by(Appointment.start_datetime.desc()).all()

    # 3. CÁLCULO DE FATURAMENTO HOJE
    revenue_today = sum((a.service.price_cents if a.service else 0) for a in services_today 
                        if a.status in ['confirmed', 'completed', 'in_progress', 'arrived']) / 100

    # 4. CÁLCULO TOTAL HISTÓRICO
    total_revenue = sum((a.service.price_cents if a.service else 0) for a in all_appointments 
                        if a.status in ['confirmed', 'completed', 'in_progress']) / 100

    # 5. LÓGICA DO GRÁFICO (Ajustada para evitar o erro de strftime anterior)
    seven_days_ago = today - timedelta(days=7)
    stats_7_days = db.session.query(
        func.date(Appointment.start_datetime),
        func.count(Appointment.id)
    ).filter(Appointment.start_datetime >= seven_days_ago)\
     .group_by(func.date(Appointment.start_datetime)).all()

    chart_labels = []
    chart_data = []
    for row in stats_7_days:
        # Tratamento seguro para SQLite (string) ou Postgres (date)
        d = row[0]
        if isinstance(d, str):
            d = datetime.strptime(d, '%Y-%m-%d')
        chart_labels.append(d.strftime('%d/%m'))
        chart_data.append(row[1])

    return render_template(
        'admin/dashboard.html', 
        services_today=services_today,  # <--- ESSA É A LISTA DA TABELA
        appointments=all_appointments, # <--- ESSA É A LISTA PARA OS CARDS
        revenue_today=revenue_today,
        total_revenue=total_revenue,
        total_appointments=len(all_appointments),
        chart_labels=chart_labels,
        chart_data=chart_data,
        now=now
    )

# --- GESTÃO DE USUÁRIOS (VERSÃO ÚNICA E CORRETA) ---

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    # Sênior: Buscamos os dados de forma separada para o template users_list.html
    # Isso resolve o incômodo de ver tudo misturado
    admins = User.query.filter_by(is_admin=True).order_by(User.name.asc()).all()
    patients = User.query.filter_by(is_admin=False).order_by(User.name.asc()).all()
    
    return render_template('admin/users_list.html', 
                           admins=admins, 
                           patients=patients)

@admin_bp.route('/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado!', 'danger')
            return redirect(url_for('admin.new_user'))

        new_u = User(name=username, email=email, is_admin=(role == 'admin'))
        new_u.set_password(password)
        db.session.add(new_u)
        db.session.commit()
        
        flash(f'Usuário {username} criado com sucesso!', 'success')
        return redirect(url_for('admin.list_users'))
    return render_template('admin/edit_user.html', user=None, title="Novo Usuário")

@admin_bp.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.name = request.form.get('username')
        user.email = request.form.get('email')
        new_role = request.form.get('role')
        
        if user.id == current_user.id and new_role == 'cliente':
            flash('Erro crítico: Você não pode remover seu próprio acesso administrativo.', 'danger')
        else:
            user.is_admin = (new_role == 'admin')
            
        db.session.commit()
        flash(f'Perfil de {user.name} atualizado!', 'success')
        return redirect(url_for('admin.list_users'))
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Segurança: Você não pode excluir sua própria conta.', 'danger')
        return redirect(url_for('admin.list_users'))
    
    # Limpa agendamentos antes de deletar (Integridade referencial)
    Appointment.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário {user.name} removido permanentemente.', 'success')
    return redirect(url_for('admin.list_users'))

# --- GESTÃO DE AGENDAMENTOS ---

@admin_bp.route('/all-appointments')
@login_required
@admin_required
def list_all_appointments():
    # Sênior: Uso de joinedload para carregar User e Service em uma única query (Performance)
    all_appts = Appointment.query.options(
        joinedload(Appointment.user), 
        joinedload(Appointment.service)
    ).order_by(Appointment.start_datetime.desc()).all()
    return render_template('admin/all_appointments.html', appointments=all_appts)

@admin_bp.route('/appointment/<int:id>/status/<string:new_status>', methods=['POST'])
@login_required
@admin_required
def update_status(id, new_status):
    appt = Appointment.query.get_or_404(id)
    
    messages = {
        'confirmed': f'Consulta de {appt.user.name} confirmada!',
        'cancelled': f'A consulta de {appt.user.name} foi cancelada.',
        'completed': f'Atendimento de {appt.user.name} finalizado!'
    }

    if new_status in messages:
        appt.status = new_status
        db.session.commit()
        flash(messages.get(new_status), 'success')
    else:
        flash('Status inválido.', 'danger')
        
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/appointment/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_appointment(id):
    appt = Appointment.query.get_or_404(id)
    db.session.delete(appt)
    db.session.commit()
    flash('Agendamento removido do histórico.', 'success')
    return redirect(url_for('admin.list_all_appointments'))

# --- GESTÃO DE SERVIÇOS ---

@admin_bp.route('/services')
@login_required
@admin_required
def list_services():
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@admin_bp.route('/service/new', methods=['GET', 'POST'])
@admin_bp.route('/service/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_service(id=None):
    service = Service.query.get_or_404(id) if id else None
    resources = Resource.query.all() 
    
    if request.method == 'POST':
        try:
            price_reais = float(request.form.get('price', 0))
            price_cents = int(round(price_reais * 100))
            
            if not service:
                service = Service()
                db.session.add(service)
            
            service.name = request.form.get('name')
            service.description = request.form.get('description')
            service.category = request.form.get('category')
            service.duration_minutes = int(request.form.get('duration'))
            service.price_cents = price_cents
            service.active = True if request.form.get('active') else False
            service.resource_id = request.form.get('resource_id')
            
            db.session.commit()
            flash(f'Serviço "{service.name}" atualizado.', 'success')
            return redirect(url_for('admin.list_services'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar serviço.', 'danger')
    
    title = "Editar Serviço" if id else "Novo Serviço"
    return render_template('admin/service_form.html', service=service, title=title, resources=resources)


#rota de filtro Ela vai buscar os agendamentos filtrando pelo ID do paciente:
@admin_bp.route('/user/<int:id>/history')
@login_required
@admin_required
def user_history(id):
    user = User.query.get_or_404(id)
    # Filtra os agendamentos apenas deste usuário
    appointments = Appointment.query.filter_by(user_id=id).order_by(Appointment.start_datetime.desc()).all()
    
    return render_template('admin/all_appointments.html', 
                           appointments=appointments, 
                           filter_user=user)
    
    
    
@admin_bp.route('/painel-tv')
@login_required
@admin_required
def tv_panel():
    from datetime import datetime
    now = datetime.now()
    today = now.date()

    # 1. ATENDIMENTOS ATIVOS (O que aparece em destaque no telão)
    # Buscamos quem está com status 'in_progress'
    atendimentos_atuais = Appointment.query.filter(
        func.date(Appointment.start_datetime) == today,
        Appointment.status == 'in_progress'
    ).options(
        joinedload(Appointment.user), 
        joinedload(Appointment.service)
    ).all()

    # 2. FILA DE ESPERA (Quem já chegou na recepção)
    # Buscamos quem está com status 'arrived' ou 'confirmed' (ainda não chamados)
    fila_espera = Appointment.query.filter(
        func.date(Appointment.start_datetime) == today,
        Appointment.status.in_(['arrived', 'confirmed'])
    ).options(
        joinedload(Appointment.user)
    ).order_by(Appointment.start_datetime.asc()).all()
    
    return render_template(
        'admin/tv_panel.html', 
        atendimentos=atendimentos_atuais, 
        espera=fila_espera, 
        now=now
    )