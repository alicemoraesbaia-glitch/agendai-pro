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
