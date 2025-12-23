from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.main import main_bp
from app.models import Service, Appointment, Resource
from datetime import datetime, timedelta, timezone
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

@main_bp.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id):
    # 1. LIMPEZA INICIAL: Remove pendentes antigos antes de qualquer lógica
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

    # Configuração de Horários
    working_hours = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]

    if request.method == 'POST':
        time_str = request.form.get('slot')
        user_phone = request.form.get('phone')

        # Validações básicas
        if not user_phone or len(user_phone) < 8:
            flash('Por favor, informe um WhatsApp válido.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))
        
        if not time_str:
            flash('Por favor, selecione um horário.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        # Cálculo de horários
        clean_time = time_str.strip()[:5]
        start_dt = datetime.combine(selected_date, datetime.strptime(clean_time, '%H:%M').time())
        end_dt = start_dt + timedelta(minutes=service.duration_minutes)

        # 2. VALIDAÇÃO DE CONFLITO DE RECURSO (Sala/Profissional)
        if Appointment.check_resource_conflict(service.id, start_dt, end_dt):
            flash('Este horário acabou de ser ocupado. Escolha outro.', 'danger')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        # 3. VALIDAÇÃO DE CONFLITO DE USUÁRIO (Evita o cliente marcar duas coisas ao mesmo tempo)
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
            print(f"Erro ao salvar agendamento: {e}")
            flash('Erro sistêmico ao processar agendamento.', 'danger')

    # --- GERAÇÃO DE SLOTS (Visualização) ---
    slots = []
    for h in working_hours:
        slot_time_obj = datetime.strptime(h, '%H:%M').time()
        slot_start = datetime.combine(selected_date, slot_time_obj)
        slot_end = slot_start + timedelta(minutes=service.duration_minutes)
        
        # O horário só está livre se o recurso estiver livre E for no futuro
        is_resource_free = not Appointment.check_resource_conflict(service.id, slot_start, slot_end)
        is_future = slot_start > now
        
        slots.append({
            'time': slot_start, 
            'available': is_resource_free and is_future
        })

    return render_template('main/book.html', service=service, slots=slots, date=date_str)

# --- FUNÇÃO DE LIMPEZA (Mantenha-a no final do arquivo ou em um utils.py) ---
def limpar_agendamentos_expirados():
    """ Cancela agendamentos pendentes com mais de 15 minutos de criação """
    limite = datetime.now() - timedelta(minutes=15)
    
    # Sênior: Usamos synchronize_session=False para performance em updates em massa
    Appointment.query.filter(
        Appointment.status == 'pending',
        Appointment.created_at <= limite
    ).update({Appointment.status: 'cancelled'}, synchronize_session=False)
    
    db.session.commit()



# --- ROTA: MEUS AGENDAMENTOS ---
@main_bp.route('/my-appointments')
@login_required
def my_appointments():
    appointments = Appointment.query.filter_by(user_id=current_user.id)\
        .order_by(Appointment.start_datetime.desc()).all()
    
    # Passamos o datetime atual em UTC para comparar com o created_at
    return render_template('main/my_appointments.html', 
                           appointments=appointments,
                           timedelta=timedelta)

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


@main_bp.route('/servicos')
def list_services():
    services = Service.query.filter_by(active=True).order_by(Service.category).all()
    
    # Sênior: Deixamos o SQL resolver o DISTINCT para poupar memória do servidor
    categories_query = db.session.query(Service.category).filter_by(active=True).distinct().all()
    categories = sorted([c[0] for c in categories_query])
    
    return render_template('main/services_catalog.html', 
                           services=services, 
                           categories=categories,
                           title="Nossos Procedimentos")
    
    
@main_bp.route('/servico/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    return render_template('main/service_detail.html', service=service)


# No seu routes.py do Blueprint 'main'
@main_bp.route('/especialistas')
def public_professionals():
    # Buscamos os médicos do banco
    professionals = Resource.query.all()
    # Usamos o template de cards premium que discutimos
    return render_template('main/professionals.html', professionals=professionals)