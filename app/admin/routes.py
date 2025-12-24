from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.admin import admin_bp
from app.models import Appointment, Service, User, Resource, AuditLog
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template


from flask import Blueprint, render_template
# ... outras importações ...

# Esta linha deve existir antes de usar @admin.route
admin = Blueprint('admin', __name__)

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

# --- Gestão de Usuários (Final do arquivo) ---

@admin_bp.route('/admin/users')
@login_required
@admin_required
def list_users():
    # Sênior: Filtramos estritamente para não misturar no dashboard
    # Admins/Staff: Quem tem flag is_admin OU role de staff/admin
    admins = User.query.filter(
        (User.is_admin == True) | (User.role.in_(['admin', 'staff']))
    ).filter(User.deleted_at == None).all()

    # Pacientes: APENAS quem tem role 'patient' E não é admin
    patients = User.query.filter_by(role='patient', is_admin=False, deleted_at=None).all()

    return render_template('admin/users.html', admins=admins, patients=patients)

@admin_bp.route('/admin/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        # AJUSTE: O seu HTML usa name="username" e name="role"
        username_input = request.form.get('username') 
        email = request.form.get('email')
        password = request.form.get('password')
        role_input = request.form.get('role') # Recebe 'cliente' ou 'admin'

        # Validação básica
        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado no sistema.', 'danger')
            return redirect(url_for('admin.new_user'))

        try:
            # Mapeamos o valor 'cliente' do HTML para 'patient' do Banco (se necessário)
            db_role = 'patient' if role_input == 'cliente' else 'admin'
            
            new_u = User(
                username=username_input, 
                name=username_input, # Salvamos o nome completo aqui também
                email=email, 
                role=db_role,
                is_admin=True if db_role == 'admin' else False
            )
            new_u.set_password(password if password else "Mudar123!")
            
            db.session.add(new_u)
            db.session.commit()
            
            flash(f'Usuário {username_input} criado com sucesso!', 'success')
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'danger')

    # Se você decidiu manter o arquivo separado, certifique-se que o nome aqui 
    # seja o nome real do arquivo (ex: new_user.html ou o seu edit_user.html)
    return render_template('admin/edit_user.html', user=None)

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
    
    # --- LÓGICA SÊNIOR: Captura o horário real de início ---
    if new_status == 'in_progress':
        # Se estamos chamando agora, gravamos o horário atual
        from datetime import datetime
        appt.actual_start = datetime.now()
    
    # Dicionário completo de mensagens
    messages = {
        'confirmed': f'Consulta de {appt.user.name} confirmada!',
        'arrived': f'{appt.user.name} acabou de chegar na recepção.',
        'in_progress': f'Atendimento de {appt.user.name} iniciado (Aparecerá na TV!).',
        'completed': f'Atendimento de {appt.user.name} finalizado com sucesso!',
        'cancelled': f'A consulta de {appt.user.name} foi cancelada.'
    }

    if new_status in messages:
        appt.status = new_status
        db.session.commit()
        flash(messages.get(new_status), 'success')
    else:
        appt.status = new_status
        db.session.commit()
        flash('Status atualizado.', 'info')
        
    return redirect(request.referrer or url_for('admin.dashboard'))

import logging # Sênior usa logs de arquivo também

import json # Certifique-se de que o import está no topo do arquivo

@admin_bp.route('/appointment/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_appointment(id):
    appt = Appointment.query.get_or_404(id)
    
    # 1. Primeiro criamos o dicionário (o snapshot)
    data_snapshot = {
        "servico": appt.service.name,
        "data_hora": appt.start_datetime.strftime('%d/%m/%Y %H:%M'),
        "cliente_id": appt.user_id,
        "valor": f"R$ {appt.service.price_cents / 100:.2f}",
        "status_final": appt.status
    }

    try:
        # 2. AQUI ENTRA O AJUSTE SÊNIOR:
        # O indent=4 cria as quebras de linha e espaços, deixando o JSON "bonito"
        json_formatado = json.dumps(data_snapshot, indent=4, ensure_ascii=False)

        log = AuditLog(
            action='DELETAR_AGENDAMENTO',
            details=json_formatado, # Salvamos a string já formatada
            admin_email=current_user.email
        )
        
        db.session.add(log)
        db.session.delete(appt)
        db.session.commit()
        
        flash('Agendamento removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao deletar agendamento.', 'danger')
        
    return redirect(request.referrer or url_for('admin.list_all_appointments'))

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
            price_raw = request.form.get('price', '0').replace(',', '.')
            price_cents = int(round(float(price_raw) * 100))
            
            if not service:
                service = Service()
                db.session.add(service)
            
            service.name = request.form.get('name')
            service.description = request.form.get('description')
            service.duration_minutes = int(request.form.get('duration', 30))
            service.price_cents = price_cents
            service.active = True if request.form.get('active') else False
            
            # --- AJUSTE SÊNIOR AQUI ---
            image_input = request.form.get('image_url')
            # Se o usuário não digitar nada, usamos 'default.png' que é o padrão da sua pasta assets
            service.image_url = image_input if image_input else 'default.png'
            
            res_id = request.form.get('resource_id')
            service.resource_id = int(res_id) if res_id and res_id != "" else None
            
            db.session.commit()
            flash(f'Serviço "{service.name}" salvo com sucesso!', 'success')
            
            # ERRO ANTERIOR: Você estava usando 'main.services' (que não existe)
            # CORREÇÃO: Redireciona para a lista de serviços do ADMIN
            return redirect(url_for('admin.list_services')) 
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar: {e}")
            flash('Erro ao processar os dados do serviço.', 'danger')
    
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
    
    
# --- PAINEL TV (A versão correta com filtros inteligentes) ---
@admin_bp.route('/painel-tv') # Use admin_bp para manter consistência
@login_required
@admin_required
def painel_tv():
    # Pegamos apenas o que é relevante para o público ver na TV
    agora = datetime.now()
    
    # 1. Atendimentos que estão acontecendo AGORA (Status 'in_progress')
    em_curso = Appointment.query.filter_by(status='in_progress').options(
        joinedload(Appointment.user), 
        joinedload(Appointment.service)
    ).all()
    
    # 2. Próximos da fila (Confirmados ou Pendentes do futuro)
    proximos = Appointment.query.filter(
        Appointment.status.in_(['confirmed', 'pending']),
        Appointment.start_datetime >= agora
    ).order_by(Appointment.start_datetime.asc()).limit(5).all()

    return render_template('admin/painel_tv.html', 
                           em_curso=em_curso, 
                           proximos=proximos)

# --- DASHBOARD DE OCUPAÇÃO (A versão operacional clara) ---
@admin_bp.route('/dashboard-ocupacao')
@login_required
@admin_required
def occupation_dashboard():
    now = datetime.now()
    hoje = now.date()
    
    # Pegamos todos de hoje para alimentar os cards e a tabela
    appts_hoje = Appointment.query.filter(
        db.func.date(Appointment.start_datetime) == hoje
    ).options(joinedload(Appointment.user), joinedload(Appointment.service)).all()

    # Passamos a lista completa para o template usar os filtros do Jinja
    return render_template('admin/occupation_dashboard.html', 
                           appointments=appts_hoje, # Mudei de 'appts' para 'appointments' para bater com o HTML que te mandei antes
                           now=now)
    
@admin_bp.route('/resources/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_resource():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        
        if not name:
            flash('O nome é obrigatório.', 'warning')
            return render_template('admin/resource_form.html', resource=None)

        try:
            new_res = Resource(name=name, category=category)
            db.session.add(new_res)
            db.session.commit()
            flash(f'Especialista {name} cadastrado com sucesso!', 'success')
            return redirect(url_for('admin.list_resources'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar recurso. Tente novamente.', 'danger')
            
    # Importante: Passar resource=None explicitamente
    return render_template('admin/resource_form.html', resource=None)

@admin_bp.route('/resource/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_resource(id):
    resource = Resource.query.get_or_404(id)
    if request.method == 'POST':
        resource.name = request.form.get('name', '').strip()
        resource.category = request.form.get('category', '').strip()
        
        try:
            db.session.commit()
            flash(f'Dados de {resource.name} atualizados!', 'success')
            return redirect(url_for('admin.list_resources'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar os dados.', 'danger')
            
    return render_template('admin/resource_form.html', resource=resource)
    
    
# Adicione ao final do seu arquivo de rotas admin
@admin_bp.route('/resources')
@login_required
@admin_required
def list_resources():
    # Lista todos os médicos/salas cadastrados
    resources = Resource.query.all()
    return render_template('admin/resources_list.html', resources=resources)
    return render_template('admin/resource_form.html', resource=resource)


@admin_bp.route('/admin/user/<int:id>/unlock', methods=['POST'])
@login_required
@admin_required
def unlock_user(id):
    user = User.query.get_or_404(id)
    user.reset_failed_attempts() # O método que já criamos no seu Model
    db.session.commit()
    flash(f'A conta de {user.name} foi desbloqueada com sucesso.', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/logs/deletados')
@login_required
@admin_required
def view_delete_logs():
    # Busca os logs mais recentes primeiro
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    return render_template('admin/logs_deletados.html', logs=logs)

