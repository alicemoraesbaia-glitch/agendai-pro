import os
from app import create_app, db
from app.models import Service

app = create_app()

with app.app_context():
    # 1. REMOVIDO: A parte que deleta arquivos foi removida para não estragar as migrações.
    # O comando 'flask db upgrade' já criou as tabelas, agora só vamos populá-las.

    print("⏳ Verificando serviços existentes...")
    
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