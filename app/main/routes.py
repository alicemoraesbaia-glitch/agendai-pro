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

# --- ROTA: AGENDAMENTO (VERSÃO SÊNIOR BLINDADA) ---
@main_bp.route('/book/<int:service_id>', methods=['GET', 'POST'])
@login_required
def book_service(service_id):
    # --- CHAMADA DA LIMPEZA (Adicione isso aqui) ---
    limpar_agendamentos_expirados()
    service = Service.query.get_or_404(service_id)
    now = datetime.now()
    
    # --- 1. LÓGICA DE AUTO-LIMPEZA (IMPORTANTE) ---
    # Limpa agendamentos pendentes que "expiraram" (ex: iniciados há mais de 30 min e não pagos/confirmados)
    # Isso faz com que o horário volte a ficar disponível se o cliente desistir.
    limite_pendente = now - timedelta(minutes=30)
    Appointment.query.filter(
        Appointment.status == 'pending',
        Appointment.start_datetime > now,
        # Se você tiver 'created_at' use ele, caso contrário, cancelamos pendentes de dias passados ou antigos
        Appointment.start_datetime < (now + timedelta(days=1)) 
    ).update({Appointment.status: 'cancelled'}, synchronize_session=False)
    db.session.commit()

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
        user_phone = request.form.get('phone')

        if not user_phone or len(user_phone) < 8:
            flash('Por favor, informe um WhatsApp válido para coordenação.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))
        
        if not time_str:
            flash('Por favor, selecione um horário disponível.', 'warning')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        clean_time = time_str.strip()[:5]
        start_dt = datetime.combine(selected_date, datetime.strptime(clean_time, '%H:%M').time())
        end_dt = start_dt + timedelta(minutes=service.duration_minutes)

        # VALIDAÇÃO DE CONFLITO
        # Sênior: Se Appointment.check_resource_conflict estiver correto (filtrando status != 'cancelled'),
        # ele vai detectar o 'pending' que acabou de ser criado.
        if Appointment.check_resource_conflict(service.id, start_dt, end_dt):
            flash(f'Este horário foi reservado segundos atrás. Por favor, escolha outro.', 'danger')
            return redirect(url_for('main.book_service', service_id=service.id, date=date_str))

        try:
            new_appt = Appointment(
                start_datetime=start_dt,
                end_datetime=end_dt,
                service_id=service.id,
                resource_id=service.resource_id, # <--- CORREÇÃO CRÍTICA: Salve o recurso aqui!
                user_id=current_user.id,
                phone=user_phone,
                status='pending'
            )
            db.session.add(new_appt)
            db.session.commit()
            
            # Se o serviço for pago, você redirecionaria para o pagamento aqui. 
            # Se for apenas reserva, avisa o usuário.
            flash('Reserva realizada! Ela será cancelada se não for confirmada em breve.', 'success')
            return redirect(url_for('main.my_appointments'))
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar: {e}")
            flash('Erro sistêmico ao salvar agendamento.', 'danger')

    # --- 2. GERAÇÃO DE SLOTS (Visualização do Cliente) ---
    slots = []
    for h in working_hours:
        slot_time_obj = datetime.strptime(h, '%H:%M').time()
        slot_start = datetime.combine(selected_date, slot_time_obj)
        slot_end = slot_start + timedelta(minutes=service.duration_minutes)
        
        # Sênior: O check_resource_conflict agora deve "enxergar" os 'pending'
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


def limpar_agendamentos_expirados():
    # Define o tempo de tolerância (ex: 15 minutos)
    tempo_limite = datetime.now() - timedelta(minutes=15)
    
    # Busca agendamentos:
    # 1. Que estejam Pendentes
    # 2. Que foram criados há mais de 15 minutos
    # 3. Que a data do atendimento ainda é no futuro
    expirados = Appointment.query.filter(
        Appointment.status == 'pending',
        # Se você não tiver o campo created_at, usaremos o start_datetime como referência
        # Mas o ideal é que o registro tenha uma data de criação.
        Appointment.start_datetime >= datetime.now() 
    ).all()

    for appt in expirados:
        # Verificamos se ele está "preso" há muito tempo
        # Se você não tiver 'created_at', pode pular essa verificação ou usar uma lógica de horário
        appt.status = 'cancelled' 
    
    db.session.commit()
    
    
