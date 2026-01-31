import requests
import os
from flask import current_app, url_for

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # Dados da API do Resend
    api_key = os.environ.get('MAIL_PASSWORD') # Sua chave re_...
    sender = os.environ.get('MAIL_DEFAULT_SENDER', 'onboarding@resend.dev')

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": sender,
                "to": user.email,
                "subject": "[Smart Agenda] Redefinição de Senha",
                "html": f"""
                <p>Olá, <strong>{user.name}</strong>,</p>
                <p>Clique no link para redefinir sua senha: <a href="{reset_url}">{reset_url}</a></p>
                """
            },
            timeout=10 # Evita que o Gunicorn mate o processo
        )
        
        if response.status_code in [200, 201, 202]:
            return True
        else:
            current_app.logger.error(f"Erro Resend API: {response.text}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Erro de Conexão API: {e}")
        return False