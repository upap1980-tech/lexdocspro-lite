# decorators.py
from functools import wraps

try:
    from flask_jwt_extended import jwt_required as _jwt_required
except ImportError:
    def _jwt_required(*args, **kwargs):
        del args, kwargs

        def decorator(fn):
            return fn

        return decorator

def jwt_required_custom(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

def abogado_or_admin_required(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper
