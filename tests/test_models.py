import pytest
from datetime import datetime, timedelta
from app.extensions import db
from app.models import User, Resource, Service, Appointment

# TESTE 1: VALIDAÇÃO DE SEGURANÇA (BLOQUEIO DE USUÁRIO)
def test_user_lockout_logic(app):
    """Verifica se o sistema bloqueia o usuário após 5 tentativas falhas"""
    with app.app_context():
        # Criamos um usuário de teste
        user = User(name="Teste", email="teste@teste.com")
        user.set_password("senha123")
        db.session.add(user)
        db.session.commit()

        # Simulamos 5 falhas seguidas
        for _ in range(5):
            user.increase_failed_attempts()
        
        # Verificamos se o status mudou para 'locked'
        assert user.is_locked is True
        assert user.failed_login_attempts == 5

# TESTE 2: VALIDAÇÃO DE REGRA DE NEGÓCIO (CONFLITO DE AGENDA)
def test_appointment_conflict(app):
    """Verifica se o sistema detecta corretamente choques de horário no mesmo recurso"""
    with app.app_context():
        # 1. Setup: Criamos a estrutura necessária (Recurso, Serviço e Usuário)
        res = Resource(name="Consultório 1", category="Geral")
        db.session.add(res)
        db.session.flush() # Faz o banco gerar o ID sem encerrar a transação
        
        srv = Service(
            name="Consulta", 
            duration_minutes=30, 
            price_cents=10000, 
            resource_id=res.id,
            category="Saúde"
        )
        db.session.add(srv)
        
        user = User(name="Paciente Teste", email="paciente@teste.com")
        user.set_password("senha_teste_123")
        db.session.add(user)
        db.session.commit()

        # 2. Criamos o primeiro agendamento (Ex: 10:00 às 10:30)
        start = datetime(2026, 1, 20, 10, 0)
        end = start + timedelta(minutes=30)
        
        apt1 = Appointment(
            user_id=user.id, 
            service_id=srv.id, 
            resource_id=res.id,
            start_datetime=start, 
            end_datetime=end, 
            status='confirmed'
        )
        db.session.add(apt1)
        db.session.commit()

        # 3. Testamos se o método 'check_resource_conflict' identifica o conflito
        # Tentamos verificar o MESMO horário que acabamos de ocupar
        has_conflict = Appointment.check_resource_conflict(srv.id, start, end)
        
        assert has_conflict is True # Se for True, o teste passa!