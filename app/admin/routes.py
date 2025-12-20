from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.admin import admin_bp
from app.models import Appointment, Service
from sqlalchemy import func
from datetime import datetime, timedelta

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash("Acesso restrito a administradores.", "danger") # Padronizado para 'danger'
        return redirect(url_for('main.index'))
    
    # 1. MÉTRICAS TOTAIS (Consistente com fuso local)
    all_appointments = Appointment.query.all()
    # A receita só conta agendamentos 'confirmed'
    total_revenue = sum((a.service.price_cents if a.service else 0) for a in all_appointments if a.status == 'confirmed') / 100
    total_appointments = len(all_appointments)
    
    # 2. DADOS PARA O GRÁFICO (Últimos 7 dias)
    # Usamos datetime.now() para manter consistência com o restante do app
    seven_days_ago = datetime.now() - timedelta(days=7)
    stats_7_days = db.session.query(
        func.date(Appointment.start_datetime),
        func.count(Appointment.id)
    ).filter(
        Appointment.start_datetime >= seven_days_ago
    ).group_by(func.date(Appointment.start_datetime)).all()

    chart_labels = [str(row[0]) for row in stats_7_days]
    chart_data = [row[1] for row in stats_7_days]

    # 3. LISTA DE HOJE
    today = datetime.now().date()
    services_today = Appointment.query.filter(
        func.date(Appointment.start_datetime) == today,
        Appointment.status != 'cancelled' # Sênior: Não listamos cancelados na agenda do dia
    ).all()

    # 4. TABELA DE GESTÃO (Todos os agendamentos)
    appointments = Appointment.query.order_by(Appointment.start_datetime.desc()).all()

    return render_template(
        'admin/dashboard.html', 
        appointments=appointments,
        total_revenue=total_revenue,
        total_appointments=total_appointments,
        chart_labels=chart_labels,
        chart_data=chart_data,
        services_today=services_today,
        now=datetime.now() # Necessário para a lógica de 'is_expired' no template
    )

# --- NOVA ROTA: CONFIRMAÇÃO ---
@admin_bp.route('/confirm-appointment/<int:appt_id>', methods=['POST'])
@login_required
def confirm_appointment(appt_id):
    if not current_user.is_admin:
        abort(403)
        
    appt = Appointment.query.get_or_404(appt_id)
    
    if appt.status == 'pending':
        appt.status = 'confirmed'
        try:
            db.session.commit()
            flash(f'Agendamento de {appt.user.name} confirmado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao confirmar agendamento.', 'danger')
            print(f"Erro Admin: {e}")
    else:
        flash('Este agendamento não pode ser confirmado.', 'warning')
        
    return redirect(url_for('admin.dashboard'))

# --- AÇÕES DE AGENDAMENTO ---
@admin_bp.route('/appointment/<int:id>/status/<string:new_status>', methods=['POST'])
@login_required
def update_status(id, new_status):
    if not current_user.is_admin:
        abort(403)
        
    appt = Appointment.query.get_or_404(id)
    if new_status in ['confirmed', 'cancelled', 'completed']:
        appt.status = new_status
        db.session.commit()
        flash(f'Agendamento de {appt.user.name} atualizado!', 'success')
    
    # Simplificado para redirecionar direto ao dashboard
    return redirect(url_for('admin.dashboard'))

# --- GESTÃO DE SERVIÇOS ---
@admin_bp.route('/services')
@login_required
def list_services():
    if not current_user.is_admin:
        abort(403)
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@admin_bp.route('/services/new', methods=['GET', 'POST'])
@login_required
def new_service():
    if not current_user.is_admin:
        abort(403)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        duration = int(request.form.get('duration'))
        price = int(float(request.form.get('price')) * 100) 
        
        service = Service(name=name, description=description, 
                         duration_minutes=duration, price_cents=price)
        db.session.add(service)
        db.session.commit()
        flash('Serviço criado com sucesso!', 'success')
        return redirect(url_for('admin.list_services'))
    
    return render_template('admin/service_form.html', title="Novo Serviço")

@admin_bp.route('/services/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_service(id):
    if not current_user.is_admin:
        abort(403)
    service = Service.query.get_or_404(id)
    if request.method == 'POST':
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.duration_minutes = int(request.form.get('duration'))
        service.price_cents = int(float(request.form.get('price')) * 100)
        service.active = 'active' in request.form
        
        db.session.commit()
        flash('Serviço atualizado!', 'success')
        return redirect(url_for('admin.list_services'))
    
    return render_template('admin/service_form.html', service=service, title="Editar Serviço")

@admin_bp.route('/service/new', methods=['GET', 'POST'])
@admin_bp.route('/service/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def manage_service(id=None):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    service = Service.query.get(id) if id else None
    
    if request.method == 'POST':
        # Conversão de Real para Centavos (Sênior: evita floats no DB)
        price_reais = float(request.form.get('price', 0))
        price_cents = int(round(price_reais * 100))
        
        if not service:
            service = Service()
            db.session.add(service)
        
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.duration_minutes = int(request.form.get('duration'))
        service.price_cents = price_cents
        # O checkbox só vai no form se estiver marcado
        service.active = True if request.form.get('active') else False
        
        db.session.commit()
        flash('Serviço atualizado com sucesso!', 'success')
        return redirect(url_for('admin.list_services'))
    
    title = "Editar Serviço" if id else "Novo Serviço"
    return render_template('admin/service_form.html', service=service, title=title)