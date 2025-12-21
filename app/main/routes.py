from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.main import main_bp
from app.models import Service, Appointment, Resource
from datetime import datetime, timedelta

# --- ROTA: HOME (INDEX) ---
@main_bp.route('/')
def index():
    # Buscamos categorias únicas para o sistema de "Exploração"
    categories = db.session.query(Service.category).filter(Service.active==True).distinct().all()
    services = Service.query.filter_by(active=True).all()
    return render_template('main/index.html', 
                           services=services, 
                           categories=[c[0] for c in categories])

# --- ROTA: EXPLORAR POR CATEGORIA (Novo Requisito) ---
@main_bp.route('/explorar/<category_name>')
def explore_category(category_name):
    services = Service.query.filter_by(category=category_name, active=True).all()
    return render_template('main/category_explore.html', 
                           category=category_name, 
                           services=services)

# --- ROTA: AGENDAMENTO (CORE LOGIC COM RF002) ---
@main_bp.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id):
    service = Service.query.get_or_404(service_id)
    now = datetime.now()
    
    # Tratamento de Data (POST e GET)
    date_str = request.form.get('date') or request.args.get('date') or now.strftime('%Y-%m-%d')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        selected_date = now.date()
        date_str = selected_date.strftime('%Y-%m-%d')

    # Configuração de Horários da Clínica
    working_hours = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]

    if request.method == 'POST':
        time_str = request.form.get('slot')
        
        if not time_str:
            flash('Por favor, selecione um horário disponível.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        clean_time = time_str.strip()[:5]
        start_dt = datetime.combine(selected_date, datetime.strptime(clean_time, '%H:%M').time())
        end_dt = start_dt + timedelta(minutes=service.duration_minutes)

        # --- RF002: VALIDAÇÃO DE CONFLITO DE RECURSO (SALA/EQUIPAMENTO) ---
        # Verificamos se a sala ou equipamento necessário está ocupado
        has_conflict = Appointment.check_resource_conflict(service.id, start_dt, end_dt)
        
        if has_conflict:
            flash(f'Infelizmente, a sala ou equipamento para este serviço já está reservado às {clean_time}.', 'danger')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        try:
            new_appt = Appointment(
                start_datetime=start_dt,
                end_datetime=end_dt,
                service_id=service.id,
                user_id=current_user.id,
                status='pending'
            )
            db.session.add(new_appt)
            db.session.commit()
            flash('Reserva realizada! Aguardando confirmação de pagamento.', 'success')
            return redirect(url_for('main.my_appointments'))
        except Exception as e:
            db.session.rollback()
            flash('Erro sistêmico ao salvar agendamento.', 'danger')

    # Lógica para renderizar os Slots (GET)
    slots = []
    for h in working_hours:
        slot_time_obj = datetime.strptime(h, '%H:%M').time()
        slot_start = datetime.combine(selected_date, slot_time_obj)
        slot_end = slot_start + timedelta(minutes=service.duration_minutes)
        
        # O slot só aparece como disponível se:
        # 1. O equipamento/sala estiver livre (check_resource_conflict)
        # 2. O horário for no futuro
        is_resource_free = not Appointment.check_resource_conflict(service.id, slot_start, slot_end)
        is_future = slot_start > now
        
        slots.append({
            'time': slot_start, 
            'available': is_resource_free and is_future
        })

    return render_template('main/book.html', service=service, slots=slots, date=date_str)

# --- ROTA: MEUS AGENDAMENTOS ---
@main_bp.route('/my-appointments')
@login_required
def my_appointments():
    appointments = Appointment.query.filter_by(user_id=current_user.id)\
        .order_by(Appointment.start_datetime.desc()).all()
    return render_template('main/my_appointments.html', appointments=appointments, now=datetime.now())

# --- ROTA: CANCELAMENTO ---
@main_bp.route('/cancel-appointment/<int:appt_id>', methods=['POST'])
@login_required
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.user_id != current_user.id: abort(403)
    
    if appt.start_datetime < datetime.now():
        flash('Consultas passadas não podem ser canceladas.', 'warning')
        return redirect(url_for('main.my_appointments'))

    appt.status = 'cancelled'
    db.session.commit()
    flash('Consulta cancelada com sucesso.', 'success')
    return redirect(url_for('main.my_appointments'))

# --- ROTA: PAGAMENTO SIMULADO ---
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