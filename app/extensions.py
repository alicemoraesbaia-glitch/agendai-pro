from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

# Instâncias das extensões (Exatamente como você enviou)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

# Configurações do Login (Adicione estas 3 linhas abaixo das instâncias)
# Elas dizem ao Flask: "Se o usuário não estiver logado, mande ele para auth.login"
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"