# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import auth_bp 
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.auth.email import send_password_reset_email

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
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        
        if user:
            if user.is_locked:
                flash('Conta bloqueada por excesso de tentativas. Redefina sua senha para desbloquear.', 'danger')
                return redirect(url_for('auth.login'))

            if user.check_password(form.password.data):
                user.reset_failed_attempts()
                db.session.commit()
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for('main.index'))
            else:
                user.increase_failed_attempts()
                db.session.commit()
                tentativas_restantes = 3 - (user.failed_login_attempts or 0)
                
                if user.is_locked:
                    flash('Conta bloqueada após 3 tentativas inválidas.', 'danger')
                else:
                    flash(f'Senha incorreta. Restam {max(0, tentativas_restantes)} tentativa(s).', 'warning')
        else:
            flash('Email ou senha inválidos.', 'danger')
            
        return redirect(url_for('auth.login'))
        
    return render_template('auth/login.html', title='Entrar', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                # O status agora é síncrono para evitar erros silenciosos
                status = send_password_reset_email(user)
                if status:
                    flash('Sucesso! Verifique sua caixa de entrada.', 'success')
                else:
                    flash('O servidor de e-mail recusou a conexão. Tente novamente mais tarde.', 'warning')
            except Exception as e:
                print(f"--- 🚨 ERRO FATAL NO SMTP: {e} ---")
                flash('Erro técnico no envio. O suporte foi notificado.', 'danger')
        else:
            flash('Se o e-mail existir, você receberá instruções.', 'info')
        
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
        user.set_password(form.password.data)
        user.reset_failed_attempts() # Já desbloqueia o usuário
        db.session.commit()
        flash('Sua senha foi redefinida com sucesso! Você já pode entrar.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)