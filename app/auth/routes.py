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
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Email ou senha inválidos', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
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
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            print(f">>> TENTANDO ENVIAR E-MAIL PARA: {user.email}") # PRINT DE TESTE
            send_password_reset_email(user)
        
        # Mantemos a mensagem para o usuário
        flash('Verifique seu e-mail para as instruções.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Recuperar Senha', form=form)



@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Verifica se o token é válido usando o método que criamos no Model User
    user = User.verify_reset_password_token(token)
    if not user:
        flash('O link de recuperação é inválido ou expirou.', 'error')
        return redirect(url_for('auth.login'))
    
    form = ResetPasswordForm() # Certifique-se de que este form está importado!
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Sua senha foi redefinida com sucesso!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Redefinir Senha', form=form)