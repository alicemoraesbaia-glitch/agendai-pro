from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.models import Appointment, Service 
from app.extensions import db               
from datetime import datetime, date, timedelta
from sqlalchemy import func

# --- DASHBOARD PRINCIPAL ---
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for('main.index'))
    
    # 1. MÉTRICAS TOTAIS
    all_appointments = Appointment.query.all()
    total_revenue = sum((a.service.price_cents if a.service else 0) for a in all_appointments if a.status == 'confirmed') / 100
    total_appointments = len(all_appointments)
    
    # 2. DADOS PARA O GRÁFICO (Corrigido para start_datetime)
    stats_7_days = db.session.query(
        func.date(Appointment.start_datetime), # <--- CORRIGIDO
        func.count(Appointment.id)
    ).filter(
        Appointment.start_datetime >= datetime.utcnow() - timedelta(days=7) # <--- CORRIGIDO
    ).group_by(func.date(Appointment.start_datetime)).all() # <--- CORRIGIDO

    chart_labels = [str(row[0]) for row in stats_7_days]
    chart_data = [row[1] for row in stats_7_days]

    # 3. LISTA DE HOJE (Corrigido para start_datetime)
    today = datetime.utcnow().date()
    services_today = Appointment.query.filter(
        func.date(Appointment.start_datetime) == today # <--- CORRIGIDO
    ).all()

    # 4. TABELA DE GESTÃO (Corrigido para start_datetime)
    appointments = Appointment.query.order_by(Appointment.start_datetime.desc()).all() # <--- CORRIGIDO

    return render_template(
        'admin/dashboard.html', 
        appointments=appointments,
        total_revenue=total_revenue,
        total_appointments=total_appointments,
        chart_labels=chart_labels,
        chart_data=chart_data,
        services_today=services_today,
        now=datetime.now()
    )

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