import os
from app import create_app, db
from app.models import Service, User

# Define o ambiente (Produção no Render ou Local)
env = os.environ.get('FLASK_CONFIG') or 'production'
app = create_app(env)

def seed():
    with app.app_context():
        print(f"DEBUG: Iniciando Bootstrap Profissional no ambiente: {env}")

        # 1. POPULANDO SERVIÇOS (Com caminhos das imagens .png)
        if Service.query.first() is None:
            print("🌱 Inserindo serviços com ativos estáticos...")
            servicos = [
                Service(
                    name="Limpeza de Pele Deep", 
                    price_cents=15000, 
                    duration_minutes=60, 
                    category="Estética", 
                    description="Limpeza profunda.", 
                    active=True,
                    image_url="assets/img/services/limpPele.png" # Caminho fixo
                ),
                Service(
                    name="Fisioterapia Esportiva", 
                    price_cents=18000, 
                    duration_minutes=45, 
                    category="Saúde", 
                    description="Recuperação muscular.", 
                    active=True,
                    image_url="assets/img/services/fisoEsport.png" # Caminho fixo
                )
            ]
            db.session.add_all(servicos)
        else:
            print("✅ Serviços já existem no banco de dados.")

        # 2. POPULANDO ADMINISTRADORES (Essencial para o acesso do Tutor)
        # 2.1 Administradora Eralice (Dona do Projeto)
        admin_alice = "alice@gmail.com"
        if User.query.filter_by(email=admin_alice).first() is None:
            print(f"👤 Criando administradora: {admin_alice}...")
            user_alice = User(
                name="Administradora Eralice", 
                email=admin_alice, 
                role='admin', 
                is_admin=True
            )
            user_alice.set_password("alice@2026")
            db.session.add(user_alice)
        
        # 2.2 Usuário de Testes para o Avaliador UNINTER
        admin_teste = "admin@teste.com"
        if User.query.filter_by(email=admin_teste).first() is None:
            print(f"👤 Criando conta para Avaliador UNINTER: {admin_teste}...")
            user_teste = User(
                name="Avaliador UNINTER", 
                email=admin_teste, 
                role='admin', 
                is_admin=True
            )
            user_teste.set_password("admin123")
            db.session.add(user_teste)

        # 3. COMMIT ÚNICO (Garante integridade total)
        try:
            db.session.commit()
            print("✨ Bootstrap Concluído! Sistema pronto para uso e avaliação.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro crítico no Bootstrap: {e}")

if __name__ == "__main__":
    seed()