"""
Analizador LexNET v2 - Versión Flexible
Soporta múltiples archivos de cualquier tipo
"""
from services.lexnet_analyzer import LexNetAnalyzer

class LexNetAnalyzerV2(LexNetAnalyzer):
    """Versión mejorada que maneja múltiples archivos flexibles"""
    
    def analizar_notificacion(self, textos: dict, archivos: list = None, provider: str = 'ollama') -> str:
        """
        Analizar notificación con archivos flexibles
        
        Args:
            textos: {
                'todos': str (todos los archivos concatenados),
                'resumen': str (si existe),
                'caratula': str (si existe),
                'principal': str (si existe),
                'adjuntos': [str] (lista de adjuntos)
            }
            archivos: [{nombre, tipo}] metadatos de archivos
            provider: Proveedor de IA
        """
        
        # Si no hay archivos clasificados, usar 'todos'
        if not textos.get('resumen') and not textos.get('principal'):
            textos['resumen'] = textos.get('todos', '')[:3000]
            textos['principal'] = textos.get('todos', '')[3000:8000]
        
        # Llamar al método padre
        return super().analizar_notificacion(textos, provider)
    
    def _generar_analisis_texto(self, datos: dict, textos: dict) -> str:
        """Sobrescribir para incluir lista de archivos procesados"""
        
        analisis_base = super()._generar_analisis_texto(datos, textos)
        
        # Añadir sección de archivos procesados si hay metadatos
        if 'archivos_procesados' in datos:
            archivos_section = "\n9. ARCHIVOS PROCESADOS\n" + "="*80 + "\n"
            for i, archivo in enumerate(datos['archivos_procesados'], 1):
                archivos_section += f"{i}. {archivo['nombre']} ({archivo['tipo']})\n"
            
            # Insertar antes del pie
            partes = analisis_base.split("="*80 + "\n" + "Generado:")
            analisis_base = partes[0] + archivos_section + "\n" + "="*80 + "\nGenerado:" + partes[1]
        
        return analisis_base
