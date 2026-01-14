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

        # 2. POPULANDO ADMINISTRADORES
        # 2.1 Administradora Eralice
        admin_alice = "alice@gmail.com"
        if User.query.filter_by(email=admin_alice).first() is None:
            print(f"👤 Criando administrador: {admin_alice}...")
            user_alice = User(name="Administradora Eralice", email=admin_alice, role='admin', is_admin=True)
            user_alice.set_password("alice@2026")
            db.session.add(user_alice)
        
        # 2.2 Usuário de Testes para o Avaliador (Sugestão Sênior)
        admin_teste = "admin@teste.com"
        if User.query.filter_by(email=admin_teste).first() is None:
            print(f"👤 Criando usuário de testes para avaliação: {admin_teste}...")
            user_teste = User(name="Avaliador UNINTER", email=admin_teste, role='admin', is_admin=True)
            user_teste.set_password("admin123") # Senha simples para o avaliador
            db.session.add(user_teste)
        else:
            print(f"✅ Usuário de testes {admin_teste} já existe.")

        # 3. COMMIT ÚNICO (Atômico)
        try:
            db.session.commit()
            print("✨ Bootstrap concluído com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro crítico no Bootstrap: {e}")

if __name__ == "__main__":
    seed()