from flask import render_template, request, flash, redirect, url_for
from app.main import main_bp
from app.models import Service, Appointment
from app.utils.availability import get_available_slots
from datetime import datetime
from flask_login import login_required, current_user
from app.extensions import db

@main_bp.route('/')
def index():
    # Buscamos os serviços ativos para exibir na landing page
    services = Service.query.filter_by(active=True).all()
    return render_template('main/index.html', services=services)


#Rota de Agendamento (O "Cérebro")
@main_bp.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id):
    service = Service.query.get_or_404(service_id)
    selected_date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    
    # Obtém os horários livres usando nossa engine
    slots = get_available_slots(selected_date, service.duration_minutes)
    
    if request.method == 'POST':
        time_str = request.form.get('slot')
        if time_str:
            # Cria o agendamento
            start_dt = datetime.strptime(f"{selected_date_str} {time_str}", '%Y-%m-%d %H:%M')
            new_appt = Appointment(
                user_id=current_user.id,
                service_id=service.id,
                start_datetime=start_dt,
                status='pending'
            )
            db.session.add(new_appt)
            db.session.commit()
            flash('Agendamento solicitado com sucesso! Aguarde confirmação.', 'success')
            return redirect(url_for('main.index'))

    return render_template('main/book.html', service=service, slots=slots, date=selected_date_str)