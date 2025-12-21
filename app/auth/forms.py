from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="O e-mail é obrigatório."), 
        Email(message="Digite um e-mail válido.")
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória.")
    ])
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    name = StringField('Nome Completo', validators=[
        DataRequired(message="O nome é obrigatório."), 
        Length(min=2, max=100, message="O nome deve ter entre 2 e 100 caracteres.")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="O e-mail é obrigatório."), 
        Email(message="Digite um e-mail válido.")
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória."), 
        Length(min=6, message="A senha deve ter no mínimo 6 caracteres.")
    ])
    confirm_password = PasswordField('Confirmar Senha', validators=[
        DataRequired(message="A confirmação de senha é obrigatória."), 
        EqualTo('password', message="As senhas devem ser iguais.")
    ])
    submit = SubmitField('Criar Conta')

    # Validação personalizada para evitar emails duplicados
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este e-mail já está cadastrado em nossa clínica.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('E-mail', validators=[
        DataRequired(message="Informe seu e-mail para recuperar a senha."), 
        Email(message="Digite um e-mail válido.")
    ])
    submit = SubmitField('Enviar Instruções')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[
        DataRequired(message="A nova senha é obrigatória."), 
        Length(min=6, message="A senha deve ter pelo menos 6 caracteres.")
    ])
    confirm_password = PasswordField('Confirme a Nova Senha', validators=[
        DataRequired(message="Confirme a sua nova senha."), 
        EqualTo('password', message="As senhas digitadas não coincidem.")
    ])
    submit = SubmitField('Redefinir Senha')