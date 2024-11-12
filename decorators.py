from functools import wraps
from flask import abort
from flask_login import current_user
from models import UserRole

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def admin_or_digitador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [UserRole.ADMIN, UserRole.DIGITADOR]:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def admin_or_digitador_or_agent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [UserRole.ADMIN, UserRole.DIGITADOR, UserRole.AGENTE]:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
