"""
Decision Engine - Lógica de decisiones automáticas
"""
import os
import shutil

class DecisionEngine:
    def __init__(self):
        pass
    
    def construir_ruta_destino(self, analisis, base_dir):
        """Construir ruta según análisis"""
        year = analisis.get('year', '2026')
        cliente = analisis.get('cliente_codigo', '2026-00_SinClasificar')
        filename = analisis.get('archivo_original', 'documento.pdf')
        
        ruta_completa = os.path.join(base_dir, year, cliente, filename)
        
        return {
            'ruta_completa': ruta_completa,
            'carpeta': os.path.dirname(ruta_completa)
        }
    
    def ejecutar_accion(self, accion, origen, destino, pendientes_dir):
        """Ejecutar acción sobre archivo"""
        try:
            dest_path = destino['ruta_completa']
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.move(origen, dest_path)
            return True
        except Exception as e:
            print(f"Error ejecutando acción: {e}")
            return False

