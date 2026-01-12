import os
from app import create_app, db
from app.models import Service

# SOLUÇÃO: Faz o seed_db.py ler a variável do Render igual ao seu run.py
env = os.environ.get('FLASK_CONFIG') or 'development'
app = create_app(env)

with app.app_context():
    print(f"DEBUG: Seed rodando no ambiente: {env}") # Ajuda a conferir no log
    print("⏳ Verificando serviços existentes...")
    
    # Restante do seu código original...
    
    # 2. Evitar duplicatas: Só insere se a tabela estiver vazia
    if Service.query.first() is None:
        print("🌱 Populando banco de dados com serviços iniciais...")
        
        servicos = [
            Service(
                name="Limpeza de Pele Deep", 
                price_cents=15000, 
                duration_minutes=60, 
                category="Estética", 
                description="Limpeza profunda com extração e hidratação.",
                active=True
            ),
            Service(
                name="Fisioterapia Esportiva", 
                price_cents=18000, 
                duration_minutes=45, 
                category="Saúde", 
                description="Recuperação muscular e prevenção de lesões.",
                active=True
            ),
            Service(
                name="Massagem Relaxante", 
                price_cents=12000, 
                duration_minutes=50, 
                category="Estética", 
                description="Alívio de stress com óleos essenciais.",
                active=True
            )
        ]

        try:
            db.session.add_all(servicos)
            db.session.commit()
            print("✨ Serviços inseridos com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao inserir dados: {e}")
    else:
        print("✅ O banco já contém serviços. Nenhuma alteração foi necessária.")