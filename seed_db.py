import os
from app import create_app, db
from app.models import Service, User

# Define o ambiente (Produção no Render ou Local)
env = os.environ.get('FLASK_CONFIG') or 'production'
app = create_app(env)

def seed():
    with app.app_context():
        print(f"DEBUG: Iniciando Bootstrap no ambiente: {env}")

        # 1. POPULANDO SERVIÇOS
        if Service.query.first() is None:
            print("🌱 Inserindo serviços iniciais...")
            servicos = [
                Service(name="Limpeza de Pele Deep", price_cents=15000, duration_minutes=60, 
                        category="Estética", description="Limpeza profunda.", active=True),
                Service(name="Fisioterapia Esportiva", price_cents=18000, duration_minutes=45, 
                        category="Saúde", description="Recuperação muscular.", active=True)
            ]
            db.session.add_all(servicos)
        else:
            print("✅ Serviços já existem.")

        # 2. POPULANDO ADMINISTRADOR (A parte que você queria unir)
        admin_email = "alice@gmail.com"
        if User.query.filter_by(email=admin_email).first() is None:
            print(f"👤 Criando administrador inicial: {admin_email}...")
            admin = User(
                name="Administradora Eralice",
                email=admin_email,
                role='admin',
                is_admin=True
            )
            admin.set_password("alice@2026") # Use sua lógica de hash do model
            db.session.add(admin)
        else:
            print(f"✅ Administrador {admin_email} já existe.")

        # 3. COMMIT ÚNICO (Atômico)
        try:
            db.session.commit()
            print("✨ Bootstrap concluído com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro crítico no Bootstrap: {e}")

if __name__ == "__main__":
    seed()