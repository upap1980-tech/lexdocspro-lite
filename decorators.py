# decorators.py
from functools import wraps

try:
    from flask_jwt_extended import jwt_required as _jwt_required, get_jwt
    from flask import jsonify
except ImportError:
    def _jwt_required(*args, **kwargs):
        del args, kwargs

        def decorator(fn):
            return fn

        return decorator
    def get_jwt():
        return {}
    def jsonify(obj):
        return obj

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
        claims = get_jwt() or {}
        rol = str(claims.get('rol', '')).upper()
        if rol not in {'ADMIN', 'ABOGADO'}:
            return jsonify({'success': False, 'error': 'Permisos insuficientes'}), 403
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt() or {}
        rol = str(claims.get('rol', '')).upper()
        if rol != 'ADMIN':
            return jsonify({'success': False, 'error': 'Permisos de ADMIN requeridos'}), 403
        return fn(*args, **kwargs)
    return wrapper
