from app import create_app
from app.extensions import db
from app.models import Service

app = create_app()

def patch():
    with app.app_context():
        services = Service.query.all()
        for s in services:
            # Preenche apenas se estiver vazio
            if not s.content:
                s.content = f"O procedimento de {s.name} utiliza as técnicas mais modernas do mercado para garantir resultados imediatos e duradouros. Nossa equipe é certificada para aplicar este protocolo com segurança."
                s.benefits = "Recuperação rápida, Resultados visíveis na primeira sessão, Melhora da autoestima"
                s.indications = "Indicado para pessoas que buscam rejuvenescimento e cuidado preventivo com a saúde."
                s.contraindications = "Gestantes e pessoas com sensibilidade cutânea aguda devem consultar um médico antes."
        
        db.session.commit()
        print("✅ Dados de marketing atualizados com sucesso!")

if __name__ == '__main__':
    patch()