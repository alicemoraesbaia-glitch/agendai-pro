import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User, Service, Resource

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

    @app.cli.command("seed-health")
    @with_appcontext
    def seed_health():
        """Popula o banco com Recursos e Serviços de Saúde/Estética."""
        
        # 1. Criar Recursos (Salas/Equipamentos)
        resources_data = [
            {'name': 'Sala de Fisioterapia 01', 'type': 'room'},
            {'name': 'Equipamento Laser Premium', 'type': 'equipment'},
            {'name': 'Sala de Estética Avançada', 'type': 'room'}
        ]
        
        for r_data in resources_data:
            if not Resource.query.filter_by(name=r_data['name']).first():
                res = Resource(name=r_data['name'], type=r_data['type'])
                db.session.add(res)
        
        db.session.commit()

        # 2. Criar Serviços vinculados aos recursos
        # Buscamos os recursos recém-criados para vincular os IDs
        sala_fisio = Resource.query.filter_by(name='Sala de Fisioterapia 01').first()
        laser = Resource.query.filter_by(name='Equipamento Laser Premium').first()

        services_data = [
            {
                'name': 'Fisioterapia Esportiva',
                'category': 'Fisioterapia',
                'duration': 50,
                'price': 15000,
                'desc': 'Tratamento focado em recuperação de lesões atléticas.',
                'resource_id': sala_fisio.id if sala_fisio else None
            },
            {
                'name': 'Depilação a Laser',
                'category': 'Estética',
                'duration': 30,
                'price': 12000,
                'desc': 'Procedimento com tecnologia de ponta para remoção de pelos.',
                'resource_id': laser.id if laser else None
            },
            {
                'name': 'Limpeza de Pele Profunda',
                'category': 'Estética',
                'duration': 60,
                'price': 18000,
                'desc': 'Remoção de impurezas e hidratação facial completa.',
                'resource_id': None
            }
        ]

        count = 0
        for s_data in services_data:
            if not Service.query.filter_by(name=s_data['name']).first():
                new_service = Service(
                    name=s_data['name'],
                    category=s_data['category'],
                    duration_minutes=s_data['duration'],
                    price_cents=s_data['price'],
                    description=s_data['desc'],
                    resource_id=s_data['resource_id'],
                    active=True
                )
                db.session.add(new_service)
                count += 1

        db.session.commit()
        click.echo(f"Finalizado! {count} serviços de saúde/estética foram adicionados.")

    @app.cli.command("db-reset")
    @with_appcontext
    def db_reset():
        """Comando de utilitário para limpar e recriar o banco (CUIDADO)."""
        if click.confirm('Isso apagará TODOS os dados. Deseja continuar?', abort=True):
            db.drop_all()
            db.create_all()
            click.echo("Banco de dados reiniciado com sucesso.")