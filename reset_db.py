from app import create_app, db
import os

app = create_app(os.getenv('FLASK_CONFIG', 'production'))
with app.app_context():
    print("⚠️  Limpando todas as tabelas do PostgreSQL...")
    db.drop_all()
    # Limpa a tabela de controle do Alembic
    db.session.execute(db.text("DROP TABLE IF EXISTS alembic_version;"))
    db.session.commit()
    print("✅ Banco de dados limpo com sucesso!")