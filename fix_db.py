from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Tenta adicionar a coluna. Se ela já existir, o SQLAlchemy avisará.
        db.session.execute(text("ALTER TABLE appointment ADD COLUMN phone VARCHAR(20)"))
        db.session.commit()
        print("✅ SUCESSO: Coluna 'phone' adicionada à tabela 'appointment'!")
    except Exception as e:
        print(f"❌ AVISO: {e}")
        print("Provavelmente a coluna já existe ou a tabela tem outro nome.")