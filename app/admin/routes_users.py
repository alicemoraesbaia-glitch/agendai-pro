# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Smart Agenda (Agendai Pro)
# Copyright (c) 2026 Eralice de Moraes Baía. Todos os direitos reservados.
# 
# Este código é PROPRIETÁRIO e CONFIDENCIAL. A reprodução, 
# distribuição ou modificação não autorizada é estritamente proibida.
# Desenvolvido para fins acadêmicos - Curso de Engenharia de Software UNINTER.
# Acadêmica: Eralice de Moraes Baía | RU: 4144099
# --------------------------------------------------------------------------
from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.admin import admin_bp
from app.models import User, Appointment
from datetime import datetime # Necessário para o Soft Delete

# AJUSTE: Importação do decorador centralizado conforme sua estrutura de pastas
from app.decorators.admin_required import admin_required

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    admins = User.query.filter(
        (User.is_admin == True) | (User.role.in_(['admin', 'staff']))
    ).filter(User.deleted_at == None).all()

    patients = User.query.filter_by(role='patient', is_admin=False, deleted_at=None).all()
    return render_template('admin/users_list.html', admins=admins, patients=patients)

@admin_bp.route('/admin/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        # 1. Captura os dados do formulário HTML (garantindo que o campo 'name' seja lido)
        name_input = request.form.get('name') 
        email = request.form.get('email')
        password = request.form.get('password')
        role_input = request.form.get('role')

        # 2. Validação de e-mail duplicado
        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado no sistema.', 'danger')
            return redirect(url_for('admin.new_user'))

        try:
            # 3. Lógica de definição de papel (Role)
            db_role = 'patient' if role_input == 'cliente' else 'admin'
            
            # 4. Instanciação do objeto User com as variáveis corretas
            new_u = User(
                name=name_input,      # Variável name_input agora coincide com a captura acima
                email=email, 
                role=db_role,
                is_admin=True if db_role == 'admin' else False
            )
            
            # 5. Define a senha (com hash automático via modelo)
            new_u.set_password(password if password else "Mudar123!")
            
            # 6. Persistência no banco de dados PostgreSQL
            db.session.add(new_u)
            db.session.commit()
            
            flash(f'Usuário {name_input} criado com sucesso!', 'success')
            return redirect(url_for('admin.list_users'))
            
        except Exception as e:
            db.session.rollback()
            # Log técnico para ajudar no debug se algo mais falhar
            flash(f'Erro ao criar usuário: {str(e)}', 'danger')

    return render_template('admin/edit_user.html', user=None)

@admin_bp.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.name = request.form.get('name') 
        user.email = request.form.get('email')
        new_role = request.form.get('role')
        
        if user.id == current_user.id and new_role != 'admin':
            flash('Erro crítico: Você não pode remover seu próprio acesso administrativo.', 'danger')
        else:
            user.role = new_role
            user.is_admin = (new_role == 'admin')

        if user.role == 'patient':
            if not user.patient_profile:
                from app.models import PatientProfile
                user.patient_profile = PatientProfile(user_id=user.id)
            user.patient_profile.cpf = request.form.get('cpf')
            user.patient_profile.insurance_plan = request.form.get('insurance_plan')
            user.patient_profile.medical_notes = request.form.get('notes_bio')
        else:
            if not user.staff_profile:
                from app.models import StaffProfile
                user.staff_profile = StaffProfile(user_id=user.id)
            user.staff_profile.professional_reg = request.form.get('professional_reg')
            user.staff_profile.specialty = request.form.get('specialty')
            user.staff_profile.bio = request.form.get('notes_bio')

        try:
            db.session.commit()
            flash(f'Perfil de {user.name} atualizado com sucesso!', 'success')
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar: {str(e)}', 'danger')

    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Segurança: Você não pode excluir sua própria conta.', 'danger')
        return redirect(url_for('admin.list_users'))
    
    # CORREÇÃO: Implementação de SOFT DELETE conforme seu relatório da UNINTER
    user.deleted_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash(f'Usuário {user.name} desativado com sucesso (Exclusão Lógica).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desativar usuário: {str(e)}', 'danger')
        
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/admin/user/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def unlock_user(id): # Mantive o nome da função para não quebrar seus links
    user = User.query.get_or_404(id)
    
    if user.is_locked:
        # Lógica de Desbloqueio
        user.is_locked = False
        user.failed_login_attempts = 0
        flash(f'Acesso de {user.name} liberado com sucesso!', 'success')
    else:
        # Lógica de Bloqueio Manual
        user.is_locked = True
        flash(f'A conta de {user.name} foi suspensa manualmente.', 'warning')
        
    db.session.commit()
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/user/<int:id>/history')
@login_required
@admin_required
def user_history(id):
    user = User.query.get_or_404(id)
    appointments = Appointment.query.filter_by(user_id=id).order_by(Appointment.start_datetime.desc()).all()
    return render_template('admin/all_appointments.html', appointments=appointments, filter_user=user)