from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.admin import admin_bp
from app.models import Appointment, Service, User
from sqlalchemy import func
from datetime import datetime, timedelta

# --- DASHBOARD PRINCIPAL ---
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash("Acesso restrito a administradores.", "danger")
        return redirect(url_for('main.index'))
    
    all_appointments = Appointment.query.all()
    total_revenue = sum((a.service.price_cents if a.service else 0) for a in all_appointments if a.status == 'confirmed') / 100
    total_appointments = len(all_appointments)
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    stats_7_days = db.session.query(
        func.date(Appointment.start_datetime),
        func.count(Appointment.id)
    ).filter(Appointment.start_datetime >= seven_days_ago).group_by(func.date(Appointment.start_datetime)).all()

    chart_labels = [str(row[0]) for row in stats_7_days]
    chart_data = [row[1] for row in stats_7_days]

    today = datetime.now().date()
    services_today = Appointment.query.filter(
        func.date(Appointment.start_datetime) == today,
        Appointment.status != 'cancelled'
    ).all()

    # Tabela de gestão para o dashboard
    appointments = Appointment.query.order_by(Appointment.start_datetime.desc()).all()

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

# --- GESTÃO DE AGENDAMENTOS (Mantendo seus nomes originais) ---

@admin_bp.route('/all-appointments')
@login_required
def list_all_appointments():
    if not current_user.is_admin:
        abort(403)
    # Eager loading para evitar erros e lentidão
    all_appts = Appointment.query.options(
        db.joinedload(Appointment.user), 
        db.joinedload(Appointment.service)
    ).order_by(Appointment.start_datetime.desc()).all()
    
    return render_template('admin/all_appointments.html', appointments=all_appts)

@admin_bp.route('/appointment/<int:id>/delete', methods=['POST'])
@login_required
def delete_appointment(id):
    if not current_user.is_admin:
        abort(403)
    appt = Appointment.query.get_or_404(id)
    db.session.delete(appt)
    db.session.commit()
    flash('Agendamento excluído com sucesso!', 'success')
    # Redireciona para a lista geral de agendamentos
    return redirect(url_for('admin.list_all_appointments'))

@admin_bp.route('/appointment/<int:id>/status/<string:new_status>', methods=['POST'])
@login_required
def update_status(id, new_status):
    if not current_user.is_admin:
        abort(403)
    appt = Appointment.query.get_or_404(id)
    if new_status in ['confirmed', 'cancelled', 'completed']:
        appt.status = new_status
        db.session.commit()
        flash(f'Status de {appt.user.username} atualizado!', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))

# --- GESTÃO DE USUÁRIOS (Nova implementação mantendo o nome list_users) ---

from werkzeug.security import generate_password_hash # Importante para a senha

@admin_bp.route('/user/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if not current_user.is_admin:
        abort(403)
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password') # Senha inicial
        
        # Verifica se o e-mail já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Este e-mail já está cadastrado!', 'danger')
            return redirect(url_for('admin.new_user'))

        # Cria o novo usuário
        # Nota: Se seu model usa 'name' em vez de 'username', ajuste abaixo
        # No trecho de criação dentro de new_user:
        new_user = User(
            name=username, # Tente trocar 'username' por 'name' aqui
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Usuário {username} criado com sucesso!', 'success')
        return redirect(url_for('admin.list_users'))
        
    return render_template('admin/edit_user.html', user=None, title="Novo Usuário")

@admin_bp.route('/users')
@login_required
def list_users():
    if not current_user.is_admin:
        abort(403)
    # Mostra todos os usuários ordenados por ID
    users = User.query.order_by(User.id.asc()).all() 
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not current_user.is_admin:
        abort(403)
        
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        # Dados básicos
        user.name = request.form.get('username')
        user.email = request.form.get('email')
        
        # LÓGICA PROFISSIONAL DE CARGOS
        new_role = request.form.get('role')
        
        # Segurança: Impede que o admin logado altere o próprio cargo para 'cliente'
        if user.id == current_user.id and new_role == 'cliente':
            flash('Erro de Segurança: Não pode remover o seu próprio acesso de Administrador.', 'danger')
        else:
            user.is_admin = (new_role == 'admin')
            
        db.session.commit()
        flash(f'Perfil de {user.name} atualizado com sucesso!', 'success')
        return redirect(url_for('admin.list_users'))
        
    return render_template('admin/edit_user.html', user=user)


@admin_bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(id)
    
    # IMPORTANTE: Deletar agendamentos do usuário antes para evitar erro de banco (FK constraint)
    Appointment.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário {user.username} removido permanentemente.', 'success')
    return redirect(url_for('admin.list_users'))

# --- GESTÃO DE SERVIÇOS (Mantendo manage_service) ---

@admin_bp.route('/services')
@login_required
def list_services():
    if not current_user.is_admin:
        abort(403)
    services = Service.query.all()
    return render_template('admin/services.html', services=services)




@admin_bp.route('/service/new', methods=['GET', 'POST'])
@admin_bp.route('/service/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def manage_service(id=None):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    # get_or_404 é melhor: se o ID não existir, ele mostra uma página 404 limpa
    service = Service.query.get_or_404(id) if id else None
    
    if request.method == 'POST':
        try:
            price_reais = float(request.form.get('price', 0))
            price_cents = int(round(price_reais * 100))
            
            if not service:
                service = Service()
                db.session.add(service)
            
            service.name = request.form.get('name')
            service.description = request.form.get('description')
            service.duration_minutes = int(request.form.get('duration'))
            service.price_cents = price_cents
            service.active = True if request.form.get('active') else False
            
            db.session.commit()
            # APENAS a mensagem de sucesso aqui
            flash(f'Serviço "{service.name}" salvo com sucesso!', 'success')
            return redirect(url_for('admin.list_services'))
            
        except Exception as e:
            # Se algo der errado (banco travado, valor inválido), a mensagem de erro entra aqui
            db.session.rollback()
            flash('Erro ao salvar o serviço. Verifique os dados e tente novamente.', 'danger')
    
    title = "Editar Serviço" if id else "Novo Serviço"
    return render_template('admin/service_form.html', service=service, title=title)