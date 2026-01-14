from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.main import main_bp
from app.models import Service, Appointment,AuditLog
from datetime import datetime, timedelta

@main_bp.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id):
    # 1. LIMPEZA INICIAL
    limpar_agendamentos_expirados()
    
    service = Service.query.get_or_404(service_id)
    now = datetime.now()

    # Tratamento de Data
    date_str = request.form.get('date') or request.args.get('date') or now.strftime('%Y-%m-%d')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        selected_date = now.date()
        date_str = selected_date.strftime('%Y-%m-%d')

    # --- LÓGICA GERAÇÃO DINÂMICA 24H ---
    working_hours = []
    current_time_iterator = datetime.combine(selected_date, datetime.min.time()) 
    end_of_day = datetime.combine(selected_date, datetime.max.time())

    while current_time_iterator + timedelta(minutes=service.duration_minutes) <= end_of_day:
        working_hours.append(current_time_iterator.strftime('%H:%M'))
        current_time_iterator += timedelta(hours=1) 

    if request.method == 'POST':
        time_str = request.form.get('slot')
        user_phone = request.form.get('phone')

        if not user_phone or len(user_phone) < 8:
            flash('Por favor, informe um WhatsApp válido.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))
        
        if not time_str:
            flash('Por favor, selecione um horário.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        clean_time = time_str.strip()[:5]
        start_dt = datetime.combine(selected_date, datetime.strptime(clean_time, '%H:%M').time())
        end_dt = start_dt + timedelta(minutes=service.duration_minutes)

        if Appointment.check_resource_conflict(service.id, start_dt, end_dt):
            flash('Este horário acabou de ser ocupado. Escolha outro.', 'danger')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        if Appointment.check_user_conflict(current_user.id, start_dt, end_dt):
            flash('Você já tem um compromisso neste horário.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        try:
            new_appt = Appointment(
                start_datetime=start_dt,
                end_datetime=end_dt,
                service_id=service.id,
                resource_id=service.resource_id, 
                user_id=current_user.id,
                phone=user_phone,
                status='pending'
            )
            db.session.add(new_appt)
            db.session.commit()
            
            flash('Reserva realizada! Confirme o pagamento para garantir sua vaga.', 'success')
            return redirect(url_for('main.my_appointments'))
        except Exception as e:
            db.session.rollback()
            flash('Erro sistêmico ao processar agendamento.', 'danger')

    # --- GERAÇÃO DE SLOTS (Visualização) ---
    slots = []
    for h in working_hours:
        slot_time_obj = datetime.strptime(h, '%H:%M').time()
        slot_start = datetime.combine(selected_date, slot_time_obj)
        slot_end = slot_start + timedelta(minutes=service.duration_minutes)
        
        is_resource_free = not Appointment.check_resource_conflict(service.id, slot_start, slot_end)
        
        if current_user.is_admin:
            is_future = True
        else:
            is_future = slot_start > now
        
        slots.append({
            'time': slot_start, 
            'available': is_resource_free and is_future
        })

    return render_template('main/book.html', service=service, slots=slots, date=date_str)

@main_bp.route('/my-appointments')
@login_required
def my_appointments():
    appointments = Appointment.query.filter_by(user_id=current_user.id)\
        .order_by(Appointment.start_datetime.desc()).all()
    
    return render_template('main/my_appointments.html', 
                           appointments=appointments,
                           timedelta=timedelta)

@main_bp.route('/cancel-appointment/<int:appt_id>', methods=['POST'])
@login_required
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    
    if appt.user_id != current_user.id: 
        abort(403)
    
    if appt.start_datetime < datetime.now():
        flash('Consultas passadas não podem ser canceladas.', 'warning')
        return redirect(url_for('main.my_appointments'))

    try:
        old_status = appt.status
        appt.status = 'cancelled'

        # Agora o Python saberá o que é AuditLog após a importação acima
        detalhes = (
            f"Cancelamento via PORTAL DO PACIENTE | "
            f"Serviço: {appt.service.name} | "
            f"Status anterior: {old_status}"
        )
        
        log = AuditLog(
            action='CANCELAR_AGENDAMENTO_PACIENTE', 
            details=detalhes, 
            admin_email=current_user.email
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash('Sua consulta foi cancelada com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        # DICA SÊNIOR: Imprima o erro no terminal local para debug
        print(f"ERRO TÉCNICO: {str(e)}") 
        flash('Erro sistêmico ao processar o cancelamento.', 'danger')

    return redirect(url_for('main.my_appointments'))

@main_bp.route('/simulate-payment/<int:appt_id>', methods=['POST'])
@login_required
def simulate_payment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.user_id != current_user.id: abort(403)

    if appt.status == 'pending':
        appt.status = 'confirmed'
        appt.payment_status = 'paid'
        db.session.commit()
        flash("Pagamento aprovado! Consulta confirmada.", "success")
    
    return redirect(url_for('main.my_appointments'))

@main_bp.route('/complete-appointment/<int:appt_id>', methods=['POST'])
@login_required
def complete_appointment(appt_id):
    if not current_user.is_admin:
        abort(403)
        
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'completed'
    db.session.commit()
    
    flash(f'Atendimento de {appt.user.name} concluído com sucesso!', 'success')
    return redirect(request.referrer or url_for('admin.dashboard_ocupacao'))

def limpar_agendamentos_expirados():
    limite = datetime.now() - timedelta(minutes=15)
    Appointment.query.filter(
        Appointment.status == 'pending',
        Appointment.created_at <= limite
    ).update({Appointment.status: 'cancelled'}, synchronize_session=False)
    db.session.commit()