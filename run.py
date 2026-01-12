import os
from app import create_app

# Adicione esta linha para ver o log no Render
env = os.environ.get('FLASK_CONFIG') or 'development'
print(f"DEBUG: O ambiente carregado é: {env}") # <--- ADICIONE ISSO

app = create_app(env)

if __name__ == "__main__":
    app.run()