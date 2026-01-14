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
from threading import Thread
from flask import render_template, current_app, url_for
from flask_mail import Message
from app.extensions import mail

def send_async_email(app, msg):
    """Envia o e-mail em segundo plano"""
    with app.app_context():
        try:
            mail.send(msg)
            print(f"✅ E-mail enviado com sucesso!")
        except Exception as e:
            print(f"❌ Erro no envio assíncrono: {e}")

def send_password_reset_email(user):
    # 1. Gera o token e a URL
    token = user.get_reset_password_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # 2. Configura a mensagem
    msg = Message(
        '[Smart Agenda] Redefinição de Senha',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    
    # Corpo em texto simples (fallback)
    msg.body = f"Olá {user.name},\n\nPara redefinir sua senha, utilize o link: {reset_url}"
    
    # Corpo em HTML com o estilo da Smart Agenda
    msg.html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
        <h2 style="color: #10b981;">Smart Agenda</h2>
        <p>Olá, <strong>{user.name}</strong>,</p>
        <p>Recebemos uma solicitação para redefinir a senha da sua conta na clínica.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" 
               style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                Redefinir Senha
            </a>
        </div>
        <p style="color: #64748b; font-size: 0.9em;">Este link é válido por 30 minutos. Se você não solicitou esta alteração, ignore este e-mail.</p>
        <hr style="border: 0; border-top: 1px solid #f1f5f9; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 0.8em; text-align: center;">Smart Agenda - Gestão Clínica Inteligente</p>
    </div>
    """
    
    # 3. Dispara a Thread
    # Usamos _get_current_object() para passar a instância real do app para a thread
    app = current_app._get_current_object()
    Thread(target=send_async_email, args=(app, msg)).start()
    
    return True