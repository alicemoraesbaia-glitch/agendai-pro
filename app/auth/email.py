from flask_mail import Message
from flask import render_template, current_app, url_for
from app.extensions import mail

def send_password_reset_email(user):
    # Gera o token para este usuário específico
    token = user.get_reset_password_token()
    
    # Cria o link completo que o usuário vai clicar
    # O _external=True é vital para gerar http://127.0.0.1... em vez de apenas /auth/...
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    msg = Message('[Smart Agenda] Redefina sua Senha',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    
    msg.body = f"Para redefinir sua senha, clique no link: {reset_url}"
    msg.html = f"""
        <p>Olá {user.name},</p>
        <p>Clique no link abaixo para redefinir sua senha:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>Se você não solicitou isso, ignore este e-mail.</p>
    """
    
    try:
        mail.send(msg)
        print(f"✅ E-mail enviado com sucesso para: {user.email}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
        return False