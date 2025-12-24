from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # --- EVOLUÇÃO SÊNIOR ---
    # Mantemos is_admin para compatibilidade com seus decorators atuais
    is_admin = db.Column(db.Boolean, default=False)
    
    # Adicionamos role para separar visualmente Pacientes de Funcionários
    # Valores sugeridos: 'patient', 'staff', 'admin'
    role = db.Column(db.String(20), default='patient', server_default='patient')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Controle de Segurança (Garantindo que comecem com 0 e não None)
    failed_login_attempts = db.Column(db.Integer, default=0, server_default='0')
    is_locked = db.Column(db.Boolean, default=False, server_default='0')

    # Relacionamentos
    appointments = db.relationship('Appointment', back_populates='user', lazy=True)

    # --- MÉTODOS DE SEGURANÇA ---
    
    def increase_failed_attempts(self):
        # A lógica defensiva que você criou é excelente.
        # Adicionei apenas o commit implícito se necessário na rota, 
        # mas aqui garantimos a integridade do dado.
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        if self.failed_login_attempts >= 5: # Sênior: 3 tentativas é muito pouco para usuários reais, 5 é o padrão de mercado.
            self.is_locked = True

    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.is_locked = False

    @property
    def username(self):
        """Retorna o email como username para garantir unicidade em sistemas de login"""
        return self.email

    # --- HELPERS SÊNIOR ---
    @property
    def is_staff(self):
        """Helper para verificar se é funcionário ou admin"""
        return self.role in ['admin', 'staff'] or self.is_admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Programação defensiva: se não houver hash, nunca autoriza
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_password_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expires_sec)
            user_id = data['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

class Resource(db.Model):
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50))  # Ex: 'Cardiologista', 'Sala 01', 'Dentista'
    # Foto do Especialista
    profile_image = db.Column(db.String(255), nullable=True, default='default-doctor.webp')
    
    services = db.relationship('Service', back_populates='resource', lazy=True)

class Service(db.Model):
    __tablename__ = 'service'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Guardamos apenas o nome do arquivo (ex: 'odonto.webp') 
    # ou a URL completa. O valor default garante que nenhum card fique em branco.
    image_url = db.Column(db.String(255), nullable=True, default='default-service.webp')
    duration_minutes = db.Column(db.Integer, nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Geral')
    
    # --- MANTIDOS: Seus campos de Marketing e Conteúdo ---
    content = db.Column(db.Text)          
    benefits = db.Column(db.Text)         
    indications = db.Column(db.Text)      
    contraindications = db.Column(db.Text)
    
    # Controle de Status
    active = db.Column(db.Boolean, default=True, index=True)

    # --- RELACIONAMENTOS (O Coração da Multi-Agenda) ---
    # Sênior: É este resource_id que dirá se o serviço é do "Médico A" ou "Médico B"
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=True)
    resource = db.relationship('Resource', back_populates='services')
    
    # Appointments com cascade para segurança de dados
    appointments = db.relationship('Appointment', back_populates='service', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Service {self.name}>'

class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    # SÊNIOR: Importante para isolar as agendas por médico/sala
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=True)
    
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    actual_start = db.Column(db.DateTime) 
    end_datetime = db.Column(db.DateTime, nullable=False)
    
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='pending')
    phone = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    user = db.relationship('User', back_populates='appointments')
    service = db.relationship('Service', back_populates='appointments')
    resource = db.relationship('Resource')

    def get_display_status(self):
        """Retorna o texto amigável do status para o HTML"""
        status_map = {
            'pending': 'Pendente',
            'confirmed': 'Confirmado',
            'in_progress': 'Em Atendimento',
            'completed': 'Concluído',
            'cancelled': 'Cancelado'
        }
        return status_map.get(self.status, self.status.capitalize())

    @staticmethod
    def check_resource_conflict(service_id, start_dt, end_dt):
        """
        LÓGICA SÊNIOR: 
        Permite agendamentos simultâneos DESDE QUE sejam em recursos diferentes.
        """
        from app.models import Service, Appointment
        service = Service.query.get(service_id)
        if not service:
            return False

        # Base da query: Horários que se sobrepõem e não estão cancelados
        query = Appointment.query.filter(
            Appointment.status != 'cancelled',
            Appointment.start_datetime < end_dt,
            Appointment.end_datetime > start_dt
        )

        # Se o serviço tem um médico/sala vinculado, checamos apenas a agenda dele
        if service.resource_id:
            query = query.filter(Appointment.resource_id == service.resource_id)
        else:
            # Se não tem recurso, ele trava o serviço globalmente (comportamento antigo)
            query = query.filter(Appointment.service_id == service_id)

        conflict = query.first()
        return conflict is not None

    @staticmethod
    def check_user_conflict(user_id, start_dt, end_dt):
        """Impede que o MESMO CLIENTE marque duas coisas ao mesmo tempo"""
        from app.models import Appointment
        conflict = Appointment.query.filter(
            Appointment.user_id == user_id,
            Appointment.status != 'cancelled',
            Appointment.start_datetime < end_dt,
            Appointment.end_datetime > start_dt
        ).first()
        return conflict is not None
    