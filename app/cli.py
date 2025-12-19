import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User, Service

def register_commands(app):
    """
    Centraliza todos os comandos CLI do aplicativo.
    Esta função é chamada no create_app() dentro do app/__init__.py
    """

    @app.cli.command("create-admin")
    @click.argument("email")
    @click.argument("password")
    @with_appcontext
    def create_admin(email, password):
        """Cria um usuário administrador inicial."""
        # Verifica se o usuário já existe para evitar erro de duplicidade
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            click.echo(f"Erro: O usuário {email} já existe.")
            return

        user = User(
            name="Administrador Master",
            email=email,
            is_admin=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Sucesso! Administrador {email} criado com êxito.")

    @app.cli.command("seed-services")
    @with_appcontext
    def seed_services():
        """Popula o banco com serviços de diversos segmentos (Uso Universal)."""
        services_data = [
            {
                'name': 'Consultoria Especializada', 
                'duration': 60, 
                'price': 20000, 
                'desc': 'Reunião estratégica para análise e planejamento.'
            },
            {
                'name': 'Atendimento Padrão', 
                'duration': 30, 
                'price': 8000, 
                'desc': 'Sessão rápida para procedimentos gerais.'
            },
            {
                'name': 'Procedimento Avançado', 
                'duration': 90, 
                'price': 35000, 
                'desc': 'Tratamento completo com acompanhamento detalhado.'
            }
        ]
        
        count = 0
        for data in services_data:
            # Só adiciona se o serviço não existir (evita duplicados em múltiplos seeds)
            if not Service.query.filter_by(name=data['name']).first():
                new_service = Service(
                    name=data['name'],
                    duration_minutes=data['duration'],
                    price_cents=data['price'],
                    description=data['desc'],
                    active=True
                )
                db.session.add(new_service)
                count += 1
        
        db.session.commit()
        click.echo(f"Finalizado! {count} novos serviços universais foram adicionados.")

    @app.cli.command("db-reset")
    @with_appcontext
    def db_reset():
        """Comando de utilitário para limpar e recriar o banco (CUIDADO)."""
        if click.confirm('Isso apagará TODOS os dados. Deseja continuar?', abort=True):
            db.drop_all()
            db.create_all()
            click.echo("Banco de dados reiniciado com sucesso.")