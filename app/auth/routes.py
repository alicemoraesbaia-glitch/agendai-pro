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
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
# ALTERAÇÃO AQUI: Importamos o auth_bp que agora reside no __init__.py
from app.auth import auth_bp 
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Parabéns, você agora é um usuário registrado!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Cadastro', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Dica Sênior: Sempre normalize o e-mail (lowercase/strip)
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        
        if user:
            # 1. Verifica se já está bloqueado antes de qualquer coisa
            if user.is_locked:
                flash('Conta bloqueada por excesso de tentativas. Redefina sua senha para desbloquear.', 'danger')
                return redirect(url_for('auth.login'))

            # 2. Tenta o login
            if user.check_password(form.password.data):
                user.reset_failed_attempts()
                db.session.commit() # Salva o reset no banco
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for('main.index'))
            else:
                # 3. Falhou: Incrementa e SALVA IMEDIATAMENTE
                user.increase_failed_attempts()
                db.session.commit() # VITAL: Garante que o contador suba no banco
                
                tentativas_restantes = 3 - (user.failed_login_attempts or 0)
                
                if user.is_locked:
                    flash('Conta bloqueada após 3 tentativas inválidas.', 'danger')
                else:
                    flash(f'Senha incorreta. Restam {tentativas_restantes} tentativa(s).', 'warning')
        else:
            # Dica Sênior: Use mensagens genéricas para não confirmar se o e-mail existe
            flash('Email ou senha inválidos.', 'danger')
            
        return redirect(url_for('auth.login'))
        
    return render_template('auth/login.html', title='Entrar', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))



# Adicione ResetPasswordRequestForm aos imports no topo do arquivo
from app.auth.email import send_password_reset_email # Verifique se este import existe!

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordRequestForm()
    
    if request.method == 'POST':
        print("--- 📥 Formulário Recebido! ---")
        if form.validate_on_submit():
            print(f"--- ✅ Formulário Válido para o e-mail: {form.email.data} ---")
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                print(f"--- 👤 Usuário encontrado: {user.username} ---")
                send_password_reset_email(user)
                flash('Um e-mail com instruções foi enviado!', 'success')
            else:
                print("--- ❌ Erro: E-mail não encontrado no banco de dados! ---")
                flash('E-mail não encontrado.', 'danger')
        else:
            print(f"--- ⚠️ Erro de Validação do Formulário: {form.errors} ---")
            flash('Dados inválidos no formulário.', 'danger')
            
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', title='Recuperar Senha', form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        flash('O link de recuperação é inválido ou expirou.', 'danger')
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Ações Sênior:
        user.set_password(form.password.data) # 1. Criptografa a nova senha
        user.reset_failed_attempts()          # 2. Zera as falhas e desbloqueia (is_locked = False)
        db.session.commit()                   # 3. Salva tudo no banco
        
        flash('Sua senha foi redefinida com sucesso! Você já pode entrar.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)