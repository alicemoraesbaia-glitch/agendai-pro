# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Smart Agenda (Agendai Pro)
# Copyright (c) 2026 Eralice de Moraes Baía. Todos os direitos reservados.
# 
# Este código é PROPRIETÁRIO e CONFIDENCIAL. A reprodução, 
# distribuição ou modificação não autorizada é estritamente proibida.
# Desenvolvido para fins acadêmicos - Curso de Engenharia de Software UNINTER.
# Acadêmica: Eralice de Moraes Baía | RU: 4144099
# --------------------------------------------------------------------------

import os
from app import create_app

# Adicione esta linha para ver o log no Render
env = os.environ.get('FLASK_CONFIG') or 'development'
print(f"DEBUG: O ambiente carregado é: {env}") # <--- ADICIONE ISSO

app = create_app(env)

if __name__ == "__main__":
    app.run()