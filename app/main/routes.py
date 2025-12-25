from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.main import main_bp
from app.models import Service, Appointment, Resource
from datetime import datetime, timedelta, timezone
# --- ROTA: HOME (INDEX) ---
@main_bp.route('/')
def index():
    # 1. Pegamos os parâmetros da URL
    query_param = request.args.get('q', '')
    category_param = request.args.get('category', '')

    # 2. Categorias para o menu (Corrigido o erro de variável local)
    # Buscamos do banco primeiro com um nome diferente
    categories_raw = db.session.query(Service.category).filter(Service.active==True).distinct().all()
    # Agora sim criamos a lista final de strings
    categories = [c[0] for c in categories_raw]

    # 3. Base da busca de serviços
    services_query = Service.query.filter_by(active=True)

    # 4. Aplicação dos filtros
    if query_param:
        services_query = services_query.filter(Service.name.ilike(f'%{query_param}%'))

    if category_param and category_param != 'Todos':
        services_query = services_query.filter_by(category=category_param)

    # 5. Executa a busca
    services = services_query.all()

    return render_template('main/index.html', 
                           services=services, 
                           categories=categories,
                           active_category=category_param,
                           search_query=query_param)

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

    # --- NOVA LÓGICA SÊNIOR: GERAÇÃO DINÂMICA 24H ---
    # Substituímos a lista fixa por um gerador que percorre o dia todo
    working_hours = []
    current_time_iterator = datetime.combine(selected_date, datetime.min.time()) # Começa 00:00
    end_of_day = datetime.combine(selected_date, datetime.max.time())

    # Enquanto houver tempo no dia para a duração do serviço
    while current_time_iterator + timedelta(minutes=service.duration_minutes) <= end_of_day:
        working_hours.append(current_time_iterator.strftime('%H:%M'))
        # Avança de 60 em 60 min (ou use service.duration_minutes para slots colados)
        current_time_iterator += timedelta(hours=1) 
    # ------------------------------------------------

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
        
        # AJUSTE SÊNIOR: Se for Admin, 'is_future' é sempre True (permite testar/lançar retroativo)
        if current_user.is_admin:
            is_future = True
        else:
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


# Use o nome do seu blueprint: main_bp
@main_bp.route('/service/delete/<int:id>', methods=['POST'])
@login_required
def delete_service(id):
    # 1. Verificação de segurança (Sênior)
    if not current_user.is_admin:
        abort(403)
        
    service = Service.query.get_or_404(id)
    
    try:
        # 2. Exclusão física do registro
        db.session.delete(service)
        db.session.commit()
        flash(f'Serviço {service.name} removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        # Se houver erro de chave estrangeira (agendamentos vinculados), avisamos o usuário
        flash('Erro ao deletar o serviço. Verifique se existem agendamentos vinculados.', 'danger')
    
    # 3. CORREÇÃO DO REDIRECT (Adaptado à sua função existente na linha 178)
    # Como a função se chama 'list_services', o endpoint é 'main.list_services'
    return redirect(url_for('main.list_services'))