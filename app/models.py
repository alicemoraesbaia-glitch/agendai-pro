from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
# Mantenha seus outros imports (datetime, generate_password_hash, etc)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    appointments = db.relationship('Appointment', back_populates='user', lazy=True)

    @property
    def username(self):
        return self.name

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # --- NOVOS MÉTODOS PARA RECUPERAÇÃO DE SENHA ---
    
    def get_reset_password_token(self):
        """Gera um token seguro baseado na SECRET_KEY do seu .env"""
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_password_token(token, expires_sec=1800):
        """Verifica se o token é válido e se não expirou (30 min)"""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, default=True)

    # Relacionamento para acessar agendamentos a partir do serviço
    appointments = db.relationship('Appointment', back_populates='service', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    end_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='pending') # 'pending', 'paid'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # AQUI ESTÁ A CORREÇÃO PARA O ERRO DO JINJA2:
    # Estes relacionamentos permitem acessar appt.user e appt.service
    user = db.relationship('User', back_populates='appointments')
    service = db.relationship('Service', back_populates='appointments')
    
    
    @property
    def is_expired(self):
        """Retorna True se o horário passou e ainda estava pendente"""
        return self.status == 'pending' and self.start_datetime < datetime.now()

    def get_display_status(self):
        """Retorna o texto do status com a lógica de expiração"""
        if self.is_expired:
            return "Expirado"
        
        status_map = {
            'pending': 'Pendente',
            'confirmed': 'Confirmado',
            'cancelled': 'Cancelado'
        }
        return status_map.get(self.status, self.status)
    
      # Método para confirmar via Admin
    def confirm(self):
        self.status = 'confirmed'
        
    # Método para confirmar via Pagamento
    def mark_as_paid(self):
        self.payment_status = 'paid'
        self.status = 'confirmed'