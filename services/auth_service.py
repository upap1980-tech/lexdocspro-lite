"""
Servicio de Autenticación para LexDocsPro LITE v2.0
Gestión segura de usuarios y JWT tokens
"""
import bcrypt
from datetime import timedelta
from typing import Optional, Dict
from models import DatabaseManager

class AuthService:
    """Servicio de autenticación y gestión de usuarios"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def hash_password(self, password: str) -> str:
        """Hash de contraseña con bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verificar contraseña contra hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def register_user(self, email: str, password: str, rol: str = 'LECTURA', nombre: str = None) -> Dict:
        """
        Registrar nuevo usuario
        
        Returns:
            Dict con success, user_id, message
        """
        # Validaciones
        if not email or not password:
            return {'success': False, 'error': 'Email y contraseña son requeridos'}
        
        if len(password) < 8:
            return {'success': False, 'error': 'La contraseña debe tener al menos 8 caracteres'}
        
        # Validar formato de email básico
        if '@' not in email or '.' not in email:
            return {'success': False, 'error': 'Email inválido'}
        
        # Verificar que rol sea válido
        valid_roles = ['ADMIN', 'ABOGADO', 'LECTURA']
        if rol not in valid_roles:
            return {'success': False, 'error': f'Rol inválido. Valores permitidos: {valid_roles}'}
        
        # Verificar si email ya existe
        existing = self.db.get_user_by_email(email)
        if existing:
            return {'success': False, 'error': 'El email ya está registrado'}
        
        # Crear usuario
        password_hash = self.hash_password(password)
        user_id = self.db.create_user(email, password_hash, rol, nombre)
        
        return {
            'success': True,
            'user_id': user_id,
            'message': 'Usuario registrado exitosamente'
        }
    
    def authenticate(self, email: str, password: str) -> Dict:
        """
        Autenticar usuario
        
        Returns:
            Dict con success, user (sin password_hash), error
        """
        if not email or not password:
            return {'success': False, 'error': 'Email y contraseña son requeridos'}
        
        user = self.db.get_user_by_email(email)
        
        if not user:
            return {'success': False, 'error': 'Credenciales inválidas'}
        
        if not user.get('activo'):
            return {'success': False, 'error': 'Usuario desactivado'}
        
        if not self.verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Credenciales inválidas'}
        
        # Actualizar último login
        self.db.update_last_login(user['id'])
        
        # Remover password_hash antes de retornar
        user_data = {k: v for k, v in user.items() if k != 'password_hash'}
        
        return {
            'success': True,
            'user': user_data
        }
    
    def get_user_safe(self, user_id: int) -> Optional[Dict]:
        """Obtener datos de usuario sin password_hash"""
        user = self.db.get_user_by_id(user_id)
        if user:
            return {k: v for k, v in user.items() if k != 'password_hash'}
        return None
    
    def validate_role(self, user_id: int, required_roles: list) -> bool:
        """
        Validar si usuario tiene uno de los roles requeridos
        
        Args:
            user_id: ID del usuario
            required_roles: Lista de roles permitidos ['ADMIN', 'ABOGADO']
        
        Returns:
            True si el usuario tiene uno de los roles
        """
        user = self.db.get_user_by_id(user_id)
        if not user or not user.get('activo'):
            return False
        
        return user.get('rol') in required_roles
