import os
from app import create_app, db
from app.models import Service, User

# Define o ambiente (Produção no Render ou Local)
env = os.environ.get('FLASK_CONFIG') or 'production'
app = create_app(env)

def seed():
    with app.app_context():
        print(f"DEBUG: Iniciando Bootstrap Profissional no ambiente: {env}")

        # 1. SINCRONIZANDO SERVIÇOS E IMAGENS
        print("🌱 Sincronizando catálogo de serviços e ativos estáticos...")
        
        # Mapeamento exato Nome -> Caminho da Imagem
        catalogo = {
            "Limpeza de Pele Deep": "assets/img/services/limpPele.png",
            "Fisioterapia Esportiva": "assets/img/services/fisoEsport.png",
            "Cardiologista": "assets/img/services/cardio.png",
            "Massagem Relaxante": "assets/img/services/massagem.png",
            "Odontologia Geral": "assets/img/services/odonto.png"
        }

        for nome, img_path in catalogo.items():
            servico = Service.query.filter_by(name=nome).first()
            if servico:
                # Se o serviço já existe, forçamos a atualização do caminho da imagem
                servico.image_url = img_path
                print(f"🔄 Caminho de imagem atualizado para: {nome}")
            else:
                # Se o serviço não existe, criamos com os dados padrão
                novo_servico = Service(
                    name=nome, 
                    price_cents=15000, 
                    duration_minutes=60, 
                    category="Saúde", 
                    active=True,
                    image_url=img_path,
                    description=f"Serviço profissional de {nome}."
                )
                db.session.add(novo_servico)
                print(f"✨ Novo serviço criado: {nome}")

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