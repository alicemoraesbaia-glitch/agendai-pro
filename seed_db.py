import os
from app import create_app, db
from app.models import Service, User

env = os.environ.get('FLASK_CONFIG') or 'production'
app = create_app(env)

def seed():
    with app.app_context():
        print(f"DEBUG: Iniciando Sincronização no ambiente: {env}")

        # 1. MAPEAMENTO DE SERVIÇOS (Apenas nomes de arquivos)
        print("🌱 Sincronizando catálogo de imagens...")
        catalogo = {
            "Limpeza de Pele Deep": "limpPele.png",
            "Fisioterapia Esportiva": "fisoEsport.png",
            "Cardiologista": "cardio.png",
            "Massagem Relaxante": "massagem.png",
            "Odontologia Geral": "odonto.png"
        }

        for nome, filename in catalogo.items():
            servico = Service.query.filter_by(name=nome).first()
            if servico:
                # Atualiza o caminho se ele estiver errado (com prefixo duplicado)
                servico.image_url = filename
                print(f"🔄 Sincronizado: {nome} -> {filename}")
            else:
                # Cria o serviço se não existir
                novo = Service(
                    name=nome, price_cents=15000, duration_minutes=60,
                    category="Geral", active=True, image_url=filename,
                    description=f"Atendimento especializado em {nome}."
                )
                db.session.add(novo)
                print(f"✨ Criado: {nome}")

        # 2. POPULANDO ADMINISTRADORES
        # 2.1 Eralice (Autora)
        if User.query.filter_by(email="alice@gmail.com").first() is None:
            admin_alice = User(name="Administradora Eralice", email="alice@gmail.com", role='admin', is_admin=True)
            admin_alice.set_password("alice@2026")
            db.session.add(admin_alice)
            print("👤 Admin Eralice criado.")

        # 2.2 Avaliador UNINTER
        if User.query.filter_by(email="admin@teste.com").first() is None:
            admin_teste = User(name="Avaliador UNINTER", email="admin@teste.com", role='admin', is_admin=True)
            admin_teste.set_password("admin123")
            db.session.add(admin_teste)
            print("👤 Admin Avaliador criado.")

        try:
            db.session.commit()
            print("✨ Bootstrap Concluído com Sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    seed()