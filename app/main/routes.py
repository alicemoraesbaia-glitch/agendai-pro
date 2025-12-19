from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.main import main_bp
from app.models import Service, Appointment
from app.utils.availability import get_available_slots
from datetime import datetime, timedelta # CORREÇÃO: Importação necessária para somar tempo

@main_bp.route('/')
def index():
    # Buscamos os serviços ativos para exibir na landing page
    services = Service.query.filter_by(active=True).all()
    return render_template('main/index.html', services=services)

@main_bp.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id):
    service = Service.query.get_or_404(service_id)
    selected_date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    
    slots = get_available_slots(selected_date, service.duration_minutes)
    
    if request.method == 'POST':
        time_str = request.form.get('slot')
        if time_str:
            # Converte string para objeto datetime
            start_dt = datetime.strptime(f"{selected_date_str} {time_str}", '%Y-%m-%d %H:%M')
            
            # CORREÇÃO SÊNIOR: Calcula o fim do agendamento
            # Sem isso, o banco gera o erro 'NOT NULL constraint failed: appointment.end_datetime'
            end_dt = start_dt + timedelta(minutes=service.duration_minutes)
            
            new_appt = Appointment(
                user_id=current_user.id,
                service_id=service.id,
                start_datetime=start_dt,
                end_datetime=end_dt, # Agora enviamos o valor obrigatório
                status='pending'
            )
            db.session.add(new_appt)
            db.session.commit()
            
            flash('Agendamento solicitado com sucesso! Verifique em seus agendamentos.', 'success')
            return redirect(url_for('main.my_appointments')) # Sênior: leva direto para onde o usuário vê o resultado

    return render_template('main/book.html', service=service, slots=slots, date=selected_date_str)

@main_bp.route('/my-appointments')
@login_required
def my_appointments():
    appointments = Appointment.query.filter_by(user_id=current_user.id)\
        .order_by(Appointment.start_datetime.desc()).all()
    
    return render_template('main/my_appointments.html', appointments=appointments, now=datetime.now())

@main_bp.route('/cancel-appointment/<int:appt_id>', methods=['POST'])
@login_required
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    
    if appt.user_id != current_user.id:
        abort(403)
    
    if appt.start_datetime < datetime.now():
        flash('Não é possível cancelar um agendamento passado.', 'error')
        return redirect(url_for('main.my_appointments'))

    appt.status = 'cancelled'
    db.session.commit()
    flash('Agendamento cancelado com sucesso.', 'success')
    return redirect(url_for('main.my_appointments'))