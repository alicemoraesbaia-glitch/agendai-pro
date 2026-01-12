import os
from app import create_app

# O sistema busca a variável 'FLASK_CONFIG'. Se não achar, usa 'development'.
env = os.environ.get('FLASK_CONFIG') or 'development'
app = create_app(env)

if __name__ == "__main__":
    # O app.run() só é usado no seu computador (Localhost)
    app.run()