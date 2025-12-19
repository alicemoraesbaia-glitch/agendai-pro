from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.models import Appointment, Service  # ADICIONADO SERVICE AQUI
from app.extensions import db                # GARANTINDO O DB
from datetime import datetime, date

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        abort(403)

    # Filtro opcional por data (padrão é hoje)
    date_str = request.args.get('date', date.today().isoformat())
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Busca todos os agendamentos do dia selecionado
    appointments = Appointment.query.filter(
        db.func.date(Appointment.start_datetime) == selected_date
    ).order_by(Appointment.start_datetime).all()

    return render_template('admin/dashboard.html', 
                           appointments=appointments, 
                           selected_date=selected_date)

@admin_bp.route('/appointment/<int:id>/status/<string:new_status>', methods=['POST'])
@login_required
def update_status(id, new_status):
    if not current_user.is_admin:
        abort(403)
        
    appt = Appointment.query.get_or_404(id)
    if new_status in ['confirmed', 'cancelled', 'completed']:
        appt.status = new_status
        db.session.commit()
        flash(f'Agendamento atualizado para {new_status}!', 'success')
    
    return redirect(url_for('admin.dashboard', date=appt.start_datetime.date().isoformat()))



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
        price = int(float(request.form.get('price')) * 100) # Converte para centavos
        
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