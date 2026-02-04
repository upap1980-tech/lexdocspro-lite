"""
Script para crear usuario administrador inicial
Ejecutar una sola vez después de la instalación
"""
import sys
import os

# Añadir directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import DatabaseManager
from services.auth_service import AuthService

def create_admin():
    """Crear usuario administrador por defecto"""
    print("="*60)
    print("🔐 CREAR USUARIO ADMINISTRADOR")
    print("="*60)
    
    db_manager = DatabaseManager()
    auth_service = AuthService(db_manager)
    
    # Datos del admin
    email = input("\n📧 Email del administrador: ").strip()
    
    if not email:
        print("❌ Email requerido")
        return
    
    password = input("🔑 Contraseña (mínimo 8 caracteres): ").strip()
    
    if not password:
        print("❌ Contraseña requerida")
        return
    
    nombre = input("👤 Nombre completo (opcional): ").strip() or None
    
    # Crear usuario ADMIN
    result = auth_service.register_user(
        email=email,
        password=password,
        rol='ADMIN',
        nombre=nombre
    )
    
    if result['success']:
        print("\n✅ Usuario administrador creado exitosamente!")
        print(f"   ID: {result['user_id']}")
        print(f"   Email: {email}")
        print(f"   Rol: ADMIN")
        print("\n🔐 Ahora puedes hacer login con estas credenciales")
    else:
        print(f"\n❌ Error: {result['error']}")
    
    print("="*60)

if __name__ == '__main__':
    create_admin()
