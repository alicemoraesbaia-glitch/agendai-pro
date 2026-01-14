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
from app.main import main_bp
from app.models import Service

@main_bp.route('/meu-perfil')
@login_required
def my_profile():
    try:
        return render_template('main/my_profile.html', user=current_user)
    except Exception as e:
        flash("Ocorreu um erro ao carregar os dados do perfil.", "danger")
        return redirect(url_for('main.index'))

@main_bp.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def edit_my_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        
        if current_user.patient_profile is None:
            from app.models import PatientProfile 
            new_profile = PatientProfile(user_id=current_user.id)
            db.session.add(new_profile)
            current_user.patient_profile = new_profile 

        current_user.patient_profile.cpf = request.form.get('cpf')
        current_user.patient_profile.insurance_plan = request.form.get('insurance_plan')
        current_user.patient_profile.medical_notes = request.form.get('medical_notes')
        
        try:
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('main.my_profile'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar os dados.', 'danger')

    return render_template('main/edit_profile.html', user=current_user)

@main_bp.route('/service/delete/<int:id>', methods=['POST'])
@login_required
def delete_service(id):
    if not current_user.is_admin:
        abort(403)
        
    service = Service.query.get_or_404(id)
    try:
        db.session.delete(service)
        db.session.commit()
        flash(f'Serviço {service.name} removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao deletar o serviço. Verifique se existem agendamentos vinculados.', 'danger')
    
    return redirect(url_for('main.list_services'))