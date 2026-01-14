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
from functools import wraps
from flask_login import current_user
from flask import abort


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # Se não estiver logado, Flask-Login já sabe lidar melhor com isso
        if not current_user.is_authenticated:
            abort(401)  # Não autenticado

        # Se estiver logado, mas não for admin
        if not getattr(current_user, 'is_admin', False):
            abort(403)  # Proibido

        return view_func(*args, **kwargs)

    return wrapper
