from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.main import main_bp
from app.models import Service, Appointment
from datetime import datetime, timedelta

@main_bp.route('/')
def index():
    services = Service.query.filter_by(active=True).all()
    return render_template('main/index.html', services=services)


@main_bp.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id):
    service = Service.query.get_or_404(service_id)
    now = datetime.now()
    
    # --- AJUSTE AQUI: Tenta pegar a data de vários lugares ---
    if request.method == 'POST':
        date_str = request.form.get('date') or request.args.get('date') or now.strftime('%Y-%m-%d')
    else:
        date_str = request.args.get('date') or now.strftime('%Y-%m-%d')

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        selected_date = now.date()
        date_str = selected_date.strftime('%Y-%m-%d')

    working_hours = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]

    # Busca ocupados apenas para a SELECTED_DATE correta
    start_day = datetime.combine(selected_date, datetime.min.time())
    end_day = datetime.combine(selected_date, datetime.max.time())
    
    occupied_slots = [
        appt.start_datetime.strftime('%H:%M') 
        for appt in Appointment.query.filter(
            Appointment.start_datetime >= start_day,
            Appointment.start_datetime <= end_day,
            Appointment.status != 'cancelled'
        ).all()
    ]

    if request.method == 'POST':
        time_str = request.form.get('slot')
        
        # DEBUG para confirmar se agora a data veio certa
        print(f">>> DATA FINAL NO POST: {selected_date}")
        print(f">>> HORA RECEBIDA: {time_str}")

        if not time_str:
            flash('Selecione um horário.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        clean_time = time_str.strip()[:5]

        if clean_time in occupied_slots:
            flash(f'O horário {clean_time} já está ocupado nesta data.', 'danger')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        try:
            start_dt = datetime.combine(selected_date, datetime.strptime(clean_time, '%H:%M').time())
            new_appt = Appointment(
                start_datetime=start_dt,
                end_datetime=start_dt + timedelta(minutes=service.duration_minutes),
                service_id=service.id,
                user_id=current_user.id,
                status='pending'
            )
            db.session.add(new_appt)
            db.session.commit()
            flash('Agendamento realizado!', 'success')
            return redirect(url_for('main.my_appointments'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar.', 'danger')

    # Para o GET
    slots = []
    for h in working_hours:
        slot_time_obj = datetime.strptime(h, '%H:%M').time()
        is_free = h not in occupied_slots
        is_future = True if selected_date > now.date() else slot_time_obj > now.time()
        slots.append({'time': datetime.combine(selected_date, slot_time_obj), 'available': is_free and is_future})

    return render_template('main/book.html', service=service, slots=slots, date=date_str)



@main_bp.route('/my-appointments')
@login_required
def my_appointments():
    appointments = Appointment.query.filter_by(user_id=current_user.id)\
        .order_by(Appointment.start_datetime.desc()).all()
    
    return render_template('main/my_appointments.html', 
                           appointments=appointments, 
                           now=datetime.now())

@main_bp.route('/cancel-appointment/<int:appt_id>', methods=['POST'])
@login_required
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    
    # VALIDAÇÃO SÊNIOR: Segurança de Propriedade
    if appt.user_id != current_user.id:
        abort(403)
        
    # VALIDAÇÃO SÊNIOR: Impede cancelar o que já passou ou já foi cancelado
    if appt.start_datetime < datetime.now():
        flash('Não é possível cancelar um agendamento passado ou expirado.', 'warning')
        return redirect(url_for('main.my_appointments'))

    try:
        appt.status = 'cancelled'
        db.session.commit()
        flash('Agendamento cancelado com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao processar cancelamento.', 'danger')
        print(f"DEBUG: {e}")
        
    return redirect(url_for('main.my_appointments'))


@main_bp.route('/simulate-payment/<int:appt_id>', methods=['POST'])
@login_required
def simulate_payment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    
    # Segurança: Apenas o dono do agendamento pode pagar
    if appt.user_id != current_user.id:
        abort(403)

    if appt.status == 'pending':
        # Na vida real, aqui você chamaria a API do Stripe/MercadoPago
        appt.status = 'confirmed'
        appt.payment_status = 'paid' # Se você criou essa coluna no banco
        
        db.session.commit()
        flash("Pagamento aprovado! Seu horário foi confirmado automaticamente.", "success")
    else:
        flash("Este agendamento não permite pagamento.", "warning")
        
    return redirect(url_for('main.my_appointments'))