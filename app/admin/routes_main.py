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
from flask import render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.admin import admin_bp
from app.models import Appointment, Service, User, Resource, AuditLog
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

# AJUSTE: Importação do decorador centralizado conforme sua estrutura de pastas
from app.decorators.admin_required import admin_required

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    from datetime import datetime, timedelta
    now = datetime.now()
    today = now.date()

    # 1. PEGAR TODOS OS AGENDAMENTOS DE HOJE
    services_today = Appointment.query.filter(
        db.func.date(Appointment.start_datetime) == today,
        Appointment.status != 'cancelled'
    ).order_by(Appointment.start_datetime.asc()).all()

    # 2. PEGAR O FEED GERAL
    all_appointments = Appointment.query.order_by(Appointment.start_datetime.desc()).all()

    # 3. CÁLCULO DE FATURAMENTO HOJE
    revenue_today = sum((a.service.price_cents if a.service else 0) for a in services_today 
                        if a.status in ['confirmed', 'completed', 'in_progress', 'arrived']) / 100

    # 4. CÁLCULO TOTAL HISTÓRICO
    total_revenue = sum((a.service.price_cents if a.service else 0) for a in all_appointments 
                        if a.status in ['confirmed', 'completed', 'in_progress']) / 100

    # 5. LÓGICA DO GRÁFICO
    seven_days_ago = today - timedelta(days=7)
    stats_7_days = db.session.query(
        func.date(Appointment.start_datetime),
        func.count(Appointment.id)
    ).filter(Appointment.start_datetime >= seven_days_ago)\
     .group_by(func.date(Appointment.start_datetime)).all()

    chart_labels = []
    chart_data = []
    for row in stats_7_days:
        d = row[0]
        if isinstance(d, str):
            d = datetime.strptime(d, '%Y-%m-%d')
        chart_labels.append(d.strftime('%d/%m'))
        chart_data.append(row[1])

    return render_template(
        'admin/dashboard.html', 
        services_today=services_today,
        appointments=all_appointments,
        revenue_today=revenue_today,
        total_revenue=total_revenue,
        total_appointments=len(all_appointments),
        chart_labels=chart_labels,
        chart_data=chart_data,
        now=now
    )

@admin_bp.route('/dashboard-ocupacao')
@login_required
@admin_required
def occupation_dashboard():
    now = datetime.now()
    hoje = now.date()
    
    appts_hoje = Appointment.query.filter(
        db.func.date(Appointment.start_datetime) == hoje
    ).options(joinedload(Appointment.user), joinedload(Appointment.service)).all()

    return render_template('admin/occupation_dashboard.html', 
                           appointments=appts_hoje,
                           now=now)

@admin_bp.route('/logs/deletados')
@login_required
@admin_required
def view_delete_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    return render_template('admin/logs_deletados.html', logs=logs)