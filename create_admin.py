from app import create_app
from app.extensions import db
from app.models import User
import sys

def create_admin_user(email, name, password):
    app = create_app()
    with app.app_context():
        # Verifica se o admin já existe para evitar duplicidade
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"Erro: O usuário com o email {email} já existe.")
            return

        try:
            # Cria a instância conforme a modelagem sênior (role='admin' e is_admin=True)
            new_admin = User(
                name=name,
                email=email,
                role='admin',
                is_admin=True
            )
            # Utiliza o método de segurança que definimos no model
            new_admin.set_password(password)
            
            db.session.add(new_admin)
            db.session.commit()
            print(f"Sucesso: Administrador '{name}' criado com êxito!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro crítico ao criar admin: {e}")

if __name__ == "__main__":
    # Você pode alterar esses valores padrão ou passar via terminal
    admin_email = "alice@gmail.com"
    admin_name = "Administrador Eralice"
    admin_pass = "alice@2026"  # Lembre-se de usar uma senha forte

    create_admin_user(admin_email, admin_name, admin_pass)