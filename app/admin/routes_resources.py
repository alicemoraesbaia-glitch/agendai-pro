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
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.extensions import db
from app.admin import admin_bp
from app.models import Resource, Service

# AJUSTE: Importação do decorador centralizado conforme sua estrutura de pastas
from app.decorators.admin_required import admin_required

@admin_bp.route('/resources')
@login_required
@admin_required
def list_resources():
    resources = Resource.query.all()
    return render_template('admin/resources_list.html', resources=resources)

@admin_bp.route('/resources/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_resource():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        
        if not name:
            flash('O nome é obrigatório.', 'warning')
            return render_template('admin/resource_form.html', resource=None)

        try:
            new_res = Resource(name=name, category=category)
            db.session.add(new_res)
            db.session.commit()
            flash(f'Especialista {name} cadastrado com sucesso!', 'success')
            return redirect(url_for('admin.list_resources'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar recurso. Tente novamente.', 'danger')
            
    return render_template('admin/resource_form.html', resource=None)

@admin_bp.route('/resource/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_resource(id):
    resource = Resource.query.get_or_404(id)
    if request.method == 'POST':
        resource.name = request.form.get('name', '').strip()
        resource.category = request.form.get('category', '').strip()
        try:
            db.session.commit()
            flash(f'Dados de {resource.name} atualizados!', 'success')
            return redirect(url_for('admin.list_resources'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar os dados.', 'danger')
            
    return render_template('admin/resource_form.html', resource=resource)

@admin_bp.route('/services')
@login_required
@admin_required
def list_services():
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@admin_bp.route('/service/new', methods=['GET', 'POST'])
@admin_bp.route('/service/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_service(id=None):
    service = Service.query.get_or_404(id) if id else None
    resources = Resource.query.all() 
    
    if request.method == 'POST':
        try:
            price_raw = request.form.get('price', '0').replace(',', '.')
            price_cents = int(round(float(price_raw) * 100))
            if not service:
                service = Service()
                db.session.add(service)
            
            service.name = request.form.get('name')
            service.description = request.form.get('description')
            service.duration_minutes = int(request.form.get('duration', 30))
            service.price_cents = price_cents
            service.active = True if request.form.get('active') else False
            image_input = request.form.get('image_url')
            service.image_url = image_input if image_input else 'default.png'
            res_id = request.form.get('resource_id')
            service.resource_id = int(res_id) if res_id and res_id != "" else None
            
            db.session.commit()
            flash(f'Serviço "{service.name}" salvo com sucesso!', 'success')
            return redirect(url_for('admin.list_services')) 
        except Exception as e:
            db.session.rollback()
            flash('Erro ao processar os dados do serviço.', 'danger')
    
    title = "Editar Serviço" if id else "Novo Serviço"
    return render_template('admin/service_form.html', service=service, title=title, resources=resources)