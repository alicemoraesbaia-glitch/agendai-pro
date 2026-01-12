from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.admin import admin_bp
from app.models import Appointment, Service, AuditLog, User
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, date
import logging

# AJUSTE: Importação do decorador centralizado
from app.decorators.admin_required import admin_required

@admin_bp.route('/all-appointments')
@login_required
@admin_required
def list_all_appointments():
    all_appts = Appointment.query.options(
        joinedload(Appointment.user), 
        joinedload(Appointment.service)
    ).order_by(Appointment.start_datetime.desc()).all()
    return render_template('admin/all_appointments.html', appointments=all_appts)

@admin_bp.route('/appointment/<int:id>/status/<string:new_status>', methods=['POST'])
@login_required
@admin_required
def update_status(id, new_status):
    appt = Appointment.query.get_or_404(id)
    hoje = date.today()
    
    if new_status == 'in_progress':
        resource_id = appt.service.resource_id if appt.service else None
        if resource_id:
            conflito = Appointment.query.join(Appointment.service).filter(
                Appointment.status == 'in_progress',
                Service.resource_id == resource_id,
                Appointment.id != id,
                db.func.date(Appointment.start_datetime) == hoje 
            ).first()
            
            if conflito:
                nome_especialista = appt.service.resource.name
                nome_paciente_atual = conflito.user.name or conflito.user.username
                logging.warning(f"Conflito: {nome_especialista} tentou atender dois ao mesmo tempo.")
                flash(f'Bloqueado: {nome_especialista} já está atendendo {nome_paciente_atual}!', 'danger')
                return redirect(request.referrer or url_for('admin.dashboard'))
        appt.actual_start = datetime.now()
    
    messages = {
        'confirmed': f'Consulta de {appt.user.name} confirmada!',
        'arrived': f'{appt.user.name} chegou.',
        'in_progress': f'Chamando {appt.user.name} no painel!',
        'completed': f'Atendimento de {appt.user.name} finalizado.',
        'cancelled': f'Consulta de {appt.user.name} cancelada.'
    }

    try:
        appt.status = new_status
        db.session.commit()
        flash(messages.get(new_status, 'Status atualizado.'), 'success' if new_status in messages else 'info')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao salvar no banco de dados.', 'danger')
        
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/appointment/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_appointment(id):
    appt = Appointment.query.get_or_404(id)
    detalhes_exclusao = (
        f"Serviço: {appt.service.name} | "
        f"Data Horário: {appt.start_datetime.strftime('%d/%m/%Y %H:%M')} | "
        f"Cliente ID: {appt.user_id} | "
        f"Valor: R$ {appt.service.price_cents / 100}"
    )
    try:
        log = AuditLog(action='DELETAR_AGENDAMENTO', details=detalhes_exclusao, admin_email=current_user.email)
        db.session.add(log)
        db.session.delete(appt)
        db.session.commit()
        flash('Agendamento removido. Ação registrada no log de auditoria.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro na operação: {str(e)}', 'danger')
    return redirect(request.referrer or url_for('admin.list_all_appointments'))

@admin_bp.route('/painel-tv')
@login_required
@admin_required
def tv_panel():
    now = datetime.now()
    today = now.date()
    atendimentos_atuais = Appointment.query.filter(
        func.date(Appointment.start_datetime) == today,
        Appointment.status == 'in_progress'
    ).options(joinedload(Appointment.user), joinedload(Appointment.service).joinedload(Service.resource)).all()

    fila_espera = Appointment.query.filter(
        func.date(Appointment.start_datetime) == today,
        Appointment.status.in_(['arrived', 'confirmed'])
    ).options(joinedload(Appointment.user), joinedload(Appointment.service).joinedload(Service.resource)).order_by(Appointment.start_datetime.asc()).all()
    
    return render_template('admin/tv_panel.html', atendimentos=atendimentos_atuais, espera=fila_espera, now=now, exibindo_amanha=False)

@admin_bp.route('/api/atendimentos_tv')
@login_required
@admin_required
def api_atendimentos_tv():
    now = datetime.now()
    today = now.date()
    atendimentos_query = Appointment.query.filter(func.date(Appointment.start_datetime) == today, Appointment.status == 'in_progress').options(joinedload(Appointment.user), joinedload(Appointment.service).joinedload(Service.resource)).all()
    espera_query = Appointment.query.filter(func.date(Appointment.start_datetime) == today, Appointment.status == 'confirmed').options(joinedload(Appointment.user), joinedload(Appointment.service)).order_by(Appointment.start_datetime.asc()).all()

    return jsonify({
        'atendimentos': [{'paciente': (a.user.name or a.user.username) if a.user else "Sem Nome", 'sala': f"SALA {atendimentos_query.index(a) + 1}", 'especialista': a.service.resource.name if (a.service and a.service.resource) else 'Equipe'} for a in atendimentos_query],
        'espera': [{'paciente': (e.user.name or e.user.username) if e.user else "Paciente Externo", 'servico': e.service.name if e.service else 'Consulta', 'horario': e.start_datetime.strftime('%H:%M') if e.start_datetime else '--:--'} for e in espera_query]
    })

@admin_bp.route('/testar-chamada-agora')
@login_required
@admin_required
def testar_chamada_agora():
    user = User.query.first()
    service = Service.query.first()
    if not user or not service: return "Erro: Cadastre usuário e serviço."
    novo_teste = Appointment(user_id=user.id, service_id=service.id, start_datetime=datetime.now(), status='in_progress')
    db.session.add(novo_teste)
    db.session.commit()
    return f"Sucesso! O paciente {user.name} está em atendimento."