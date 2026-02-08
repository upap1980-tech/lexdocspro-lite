"""
Blueprint de Autenticación - Endpoints REST
LexDocsPro LITE v2.0
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import timedelta
from services.auth_service import AuthService, AuthDB

# Crear blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Inicializar servicios
db_manager = AuthDB()
auth_service = AuthService(db_manager)

# ==========================================
# ENDPOINTS PÚBLICOS
# ==========================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registro de nuevo usuario
    
    Body:
        {
            "email": "usuario@example.com",
            "password": "contraseña123",
            "nombre": "Nombre Apellidos" (opcional),
            "rol": "LECTURA" (opcional, default: LECTURA)
        }
    
    Roles disponibles: ADMIN, ABOGADO, LECTURA
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400
        
        email = data.get('email')
        password = data.get('password')
        nombre = data.get('nombre')
        rol = data.get('rol', 'LECTURA')
        
        result = auth_service.register_user(email, password, rol, nombre)
        
        if result['success']:
            # Log de auditoría
            db_manager.log_action(
                user_id=result['user_id'],
                action='USER_REGISTERED',
                ip_address=request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'user_id': result['user_id']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
    
    except Exception as e:
        print(f"❌ Error en registro: {str(e)}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login de usuario
    
    Body:
        {
            "email": "usuario@example.com",
            "password": "contraseña123"
        }
    
    Returns:
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "user": {...}
        }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        result = auth_service.authenticate(email, password)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 401
        
        user = result['user']
        
        # Crear tokens JWT
        access_token = create_access_token(
            identity=user['id'],
            additional_claims={'rol': user['rol'], 'email': user['email']}
        )
        refresh_token = create_refresh_token(identity=user['id'])
        
        # Log de auditoría
        db_manager.log_action(
            user_id=user['id'],
            action='USER_LOGIN',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user
        }), 200
    
    except Exception as e:
        print(f"❌ Error en login: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==========================================
# ENDPOINTS PROTEGIDOS (requieren JWT)
# ==========================================

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout de usuario (añade token a blacklist)
    
    Headers:
        Authorization: Bearer <token>
    """
    try:
        jti = get_jwt()['jti']
        user_id = get_jwt_identity()
        
        # Añadir token a blacklist
        db_manager.add_to_blacklist(jti)
        
        # Log de auditoría
        db_manager.log_action(
            user_id=user_id,
            action='USER_LOGOUT',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        }), 200
    
    except Exception as e:
        print(f"❌ Error en logout: {str(e)}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/whoami', methods=['GET'])
@jwt_required()
def whoami():
    """
    Obtener información del usuario actual
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        {
            "user": {
                "id": 1,
                "email": "...",
                "rol": "...",
                ...
            }
        }
    """
    try:
        user_id = get_jwt_identity()
        user = auth_service.get_user_safe(user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'user': user
        }), 200
    
    except Exception as e:
        print(f"❌ Error en whoami: {str(e)}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refrescar access token usando refresh token
    
    Headers:
        Authorization: Bearer <refresh_token>
    
    Returns:
        {
            "access_token": "eyJ..."
        }
    """
    try:
        user_id = get_jwt_identity()
        user = db_manager.get_user_by_id(user_id)
        
        if not user or not user.get('activo'):
            return jsonify({'error': 'Usuario no válido'}), 401
        
        # Crear nuevo access token
        access_token = create_access_token(
            identity=user_id,
            additional_claims={'rol': user['rol'], 'email': user['email']}
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200
    
    except Exception as e:
        print(f"❌ Error en refresh: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==========================================
# ENDPOINTS ADMIN (solo ADMIN)
# ==========================================

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """
    Listar todos los usuarios (solo ADMIN)
    
    Headers:
        Authorization: Bearer <token>
    """
    try:
        user_id = get_jwt_identity()
        
        # Verificar que sea ADMIN
        if not auth_service.validate_role(user_id, ['ADMIN']):
            return jsonify({'error': 'Acceso denegado. Solo ADMIN'}), 403
        
        users = db_manager.list_users()
        
        return jsonify({
            'success': True,
            'users': users
        }), 200
    
    except Exception as e:
        print(f"❌ Error listando usuarios: {str(e)}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/users/<int:target_user_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_user(target_user_id):
    """
    Desactivar usuario (solo ADMIN)
    
    Headers:
        Authorization: Bearer <token>
    """
    try:
        user_id = get_jwt_identity()
        
        # Verificar que sea ADMIN
        if not auth_service.validate_role(user_id, ['ADMIN']):
            return jsonify({'error': 'Acceso denegado. Solo ADMIN'}), 403
        
        # No permitir desactivarse a sí mismo
        if user_id == target_user_id:
            return jsonify({'error': 'No puedes desactivar tu propia cuenta'}), 400
        
        db_manager.deactivate_user(target_user_id)
        
        # Log de auditoría
        db_manager.log_action(
            user_id=user_id,
            action=f'DEACTIVATED_USER_{target_user_id}',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': 'Usuario desactivado'
        }), 200
    
    except Exception as e:
        print(f"❌ Error desactivando usuario: {str(e)}")
        return jsonify({'error': str(e)}), 500
