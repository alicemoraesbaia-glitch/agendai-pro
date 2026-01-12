#Configurações e Fixtures (Coração dos testes)
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Resource, Service

@pytest.fixture
def app():
    # Cria a instância da aplicação para teste
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", # Banco volátil
        "WTF_CSRF_ENABLED": False # Facilita testes de formulário
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
  
#O arquivo conftest.py serve para criar um banco de dados temporário (em memória) para que seus testes não apaguem seus dados reais.