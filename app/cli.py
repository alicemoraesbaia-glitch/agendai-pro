import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User

def register_commands(app):
    @app.cli.command("create-admin")
    @click.argument("email")
    @click.argument("password")
    @with_appcontext
    def create_admin(email, password):
        user = User(name="Admin", email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin {email} criado com sucesso!")