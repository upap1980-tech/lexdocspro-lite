#!/usr/bin/env python3
"""
🤖 Auto-Procesador PRO de Documentos Legales
Monitorea PENDIENTES_LEXDOCS y procesa automáticamente con IA
Integrado con Base de Datos y Dashboard Web
"""

import os
import sys
import time
import sqlite3
import shutil
import requests
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

# ============================================
# CONFIGURACIÓN
# ============================================

PENDIENTES_DIR = os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS')
EXPEDIENTES_DIR = os.path.expanduser('~/Desktop/EXPEDIENTES_LEXDOCS')
API_URL = 'http://localhost:5011'
DB_PATH = 'lexdocs_autoprocesador.db'

# Umbrales de confianza
UMBRAL_AUTO = 0.85      # >85% → Procesar automáticamente
UMBRAL_REVISION = 0.60  # 60-85% → Requiere revisión
# <60% → Error / Revisión manual

# ============================================
# BASE DE DATOS
# ============================================

def init_database():
    """Inicializar base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Tabla documentos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archivo_original TEXT NOT NULL,
            ruta_temporal TEXT,
            ruta_definitiva TEXT,
            cliente_codigo TEXT,
            cliente_detectado TEXT,
            tipo_documento TEXT,
            fecha_documento TEXT,
            fecha_procesamiento TEXT NOT NULL,
            estado TEXT NOT NULL,
            confianza_ia REAL,
            proveedor_ia TEXT,
            usuario_modifico INTEGER DEFAULT 0,
            notas TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    
    # Tabla clientes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            carpeta TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    # Tabla logs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            nivel TEXT NOT NULL,
            origen TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            documento_id INTEGER,
            FOREIGN KEY (documento_id) REFERENCES documentos(id)
        )
    """)
    
    conn.commit()
    conn.close()

def registrar_log(nivel, origen, mensaje, doc_id=None):
    """Registrar evento en logs"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO logs (timestamp, nivel, origen, mensaje, documento_id)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), nivel, origen, mensaje, doc_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error registrando log: {e}")

def registrar_documento(archivo, metadata, estado, confianza):
    """Registrar documento en BD"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        hoy = datetime.now().strftime('%Y%m%d')
        timestamp = datetime.now().isoformat()
        
        cur.execute("""
            INSERT INTO documentos (
                archivo_original, ruta_temporal, cliente_detectado,
                tipo_documento, fecha_documento, fecha_procesamiento,
                estado, confianza_ia, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            os.path.basename(archivo),
            archivo,
            metadata.get('nombre_cliente'),
            metadata.get('tipo_documento'),
            metadata.get('fecha_documento'),
            hoy,
            estado,
            confianza,
            timestamp
        ))
        
        doc_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        return doc_id
    except Exception as e:
        print(f"⚠️ Error registrando documento: {e}")
        return None

def actualizar_estado_documento(doc_id, estado, ruta_definitiva=None):
    """Actualizar estado de documento"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        if ruta_definitiva:
            cur.execute("""
                UPDATE documentos 
                SET estado = ?, ruta_definitiva = ?
                WHERE id = ?
            """, (estado, ruta_definitiva, doc_id))
        else:
            cur.execute("""
                UPDATE documentos 
                SET estado = ?
                WHERE id = ?
            """, (estado, doc_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error actualizando estado: {e}")

# ============================================
# MOTOR DE DECISIONES
# ============================================

def calcular_confianza(metadata):
    """Calcular nivel de confianza del análisis IA"""
    confianza = 0.5  # Base
    
    # Factor 1: Cliente identificado
    if metadata.get('nombre_cliente') and metadata['nombre_cliente'] != 'DESCONOCIDO':
        confianza += 0.25
    
    # Factor 2: Tipo de documento claro
    tipos_validos = ['notificacion_lexnet', 'auto', 'sentencia', 'demanda', 'diligencias_urgentes']
    if metadata.get('tipo_documento') in tipos_validos:
        confianza += 0.15
    
    # Factor 3: Fecha identificada
    if metadata.get('fecha_documento'):
        confianza += 0.10
    
    # Factor 4: Confianza reportada por IA
    if metadata.get('confianza') == 'alta':
        confianza += 0.15
    elif metadata.get('confianza') == 'media':
        confianza += 0.05
    
    return min(confianza, 1.0)

def decidir_accion(confianza, metadata):
    """Decidir qué hacer según confianza"""
    if confianza >= UMBRAL_AUTO:
        return 'auto_process', '✅ Alta confianza - Procesamiento automático'
    elif confianza >= UMBRAL_REVISION:
        return 'review', '⚠️ Confianza media - Requiere revisión'
    else:
        return 'manual', '❌ Baja confianza - Revisión manual'

def construir_ruta_destino(metadata):
    """Construir ruta de destino según análisis"""
    año = metadata.get('ano', str(datetime.now().year))
    cliente = metadata.get('nombre_cliente', 'SIN_CLASIFICAR')
    tipo = metadata.get('tipo_documento', 'Otros')
    
    # Normalizar cliente (formato: 2026-01 Nombre Cliente)
    cliente_codigo = f"{año}-01"  # Simplificado, mejorar con lógica de códigos
    carpeta_cliente = f"{cliente_codigo} {cliente}"
    
    # Subcarpeta según tipo
    subcarpetas = {
        'notificacion_lexnet': 'Notificaciones',
        'auto': 'Autos',
        'sentencia': 'Sentencias',
        'demanda': 'Demandas',
        'diligencias_urgentes': 'Diligencias'
    }
    subcarpeta = subcarpetas.get(tipo, 'Otros')
    
    ruta = os.path.join(EXPEDIENTES_DIR, año, carpeta_cliente, subcarpeta)
    os.makedirs(ruta, exist_ok=True)
    
    return ruta, carpeta_cliente

def mover_a_revision_manual(archivo):
    """Mover documento a carpeta de revisión manual"""
    manual_dir = os.path.join(PENDIENTES_DIR, 'REVISAR_MANUAL')
    os.makedirs(manual_dir, exist_ok=True)
    
    destino = os.path.join(manual_dir, os.path.basename(archivo))
    shutil.move(archivo, destino)
    
    return destino

# ============================================
# NOTIFICACIONES macOS
# ============================================

def notificar_macos(titulo, mensaje, sonido='default'):
    """Mostrar notificación macOS"""
    try:
        # Escapar comillas en el mensaje
        mensaje_escaped = mensaje.replace("'", "\\'").replace('"', '\\"')
        titulo_escaped = titulo.replace("'", "\\'").replace('"', '\\"')
        
        os.system(f'''
            osascript -e 'display notification "{mensaje_escaped}" with title "{titulo_escaped}" sound name "{sonido}"'
        ''')
    except Exception as e:
        print(f"⚠️ Error en notificación: {e}")

# ============================================
# PROCESADOR DE DOCUMENTOS
# ============================================

class DocumentHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # Ignorar archivos temporales y ocultos
        if filename.startswith('.') or filename.endswith('.tmp'):
            return
        
        # Solo procesar PDFs
        if not filename.lower().endswith('.pdf'):
            print(f"⏭️ Ignorando archivo no-PDF: {filename}")
            return
        
        print(f"\n{'='*70}")
        print(f"📄 NUEVO DOCUMENTO: {filename}")
        print(f"{'='*70}")
        
        # Esperar a que termine de copiarse
        time.sleep(3)
        
        self.procesar_documento(filepath)
    
    def procesar_documento(self, filepath):
        """Procesar documento completo"""
        filename = os.path.basename(filepath)
        
        try:
            # PASO 1: Analizar con IA
            print("🔍 Analizando con IA Multi-Proveedor...")
            
            with open(filepath, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f'{API_URL}/api/document/smart-analyze',
                    files=files,
                    timeout=120  # 2 minutos máximo
                )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
            
            data = response.json()
            
            if not data.get('success'):
                raise Exception(data.get('error', 'Análisis falló'))
            
            # PASO 2: Extraer información
            metadata = data['metadata']
            cliente_propuesto = data['cliente_propuesto']
            
            print(f"\n📊 ANÁLISIS COMPLETADO:")
            print(f"   Cliente: {metadata.get('nombre_cliente', 'DESCONOCIDO')}")
            print(f"   Tipo: {metadata.get('tipo_documento', 'N/A')}")
            print(f"   Fecha: {metadata.get('fecha_documento', 'N/A')}")
            print(f"   Confianza IA: {metadata.get('confianza', 'N/A')}")
            
            # PASO 3: Calcular confianza numérica
            confianza = calcular_confianza(metadata)
            print(f"\n🎯 Confianza calculada: {confianza:.1%}")
            
            # PASO 4: Decidir acción
            accion, razon = decidir_accion(confianza, metadata)
            print(f"🤖 Decisión: {razon}")
            
            # PASO 5: Ejecutar acción
            if accion == 'auto_process':
                # Procesamiento automático
                print("\n✅ PROCESANDO AUTOMÁTICAMENTE...")
                
                # Guardar en BD
                doc_id = registrar_documento(filepath, metadata, 'auto', confianza)
                registrar_log('info', 'auto_procesar', 
                            f"Procesamiento automático: {filename}", doc_id)
                
                # Construir ruta destino
                ruta_destino, carpeta_cliente = construir_ruta_destino(metadata)
                
                # Generar nombre de archivo
                fecha_str = metadata.get('fecha_documento', '').replace('/', '-') or \
                           datetime.now().strftime('%Y-%m-%d')
                tipo_str = metadata.get('tipo_documento', 'documento').replace('_', '-')
                nombre_final = f"{fecha_str}_{tipo_str}.pdf"
                ruta_completa = os.path.join(ruta_destino, nombre_final)
                
                # Mover archivo
                shutil.move(filepath, ruta_completa)
                
                # Actualizar BD
                actualizar_estado_documento(doc_id, 'aprobado', ruta_completa)
                
                print(f"✅ Guardado en: {ruta_completa}")
                registrar_log('info', 'auto_procesar', 
                            f"Guardado en: {ruta_completa}", doc_id)
                
                # Notificación
                notificar_macos(
                    "✅ Documento Procesado",
                    f"{cliente_propuesto.get('nombre', 'Cliente')}\n{tipo_str}",
                    'Glass'
                )
            
            elif accion == 'review':
                # Requiere revisión
                print("\n⚠️ REQUIERE REVISIÓN HUMANA...")
                
                # Guardar en BD
                doc_id = registrar_documento(filepath, metadata, 'revision', confianza)
                registrar_log('warning', 'auto_procesar', 
                            f"Requiere revisión: {filename}", doc_id)
                
                print(f"📋 Documento #{doc_id} en cola de revisión")
                print("💻 Revisa en: http://localhost:5011 → Auto-Procesador")
                
                # Notificación
                notificar_macos(
                    "⚠️ Revisión Requerida",
                    f"{filename}\nConfianza: {confianza:.0%}",
                    'default'
                )
            
            else:  # manual
                # Confianza muy baja
                print("\n❌ CONFIANZA BAJA - Revisión manual...")
                
                # Mover a REVISAR_MANUAL
                destino = mover_a_revision_manual(filepath)
                
                # Guardar en BD
                doc_id = registrar_documento(filepath, metadata, 'error', confianza)
                actualizar_estado_documento(doc_id, 'error', destino)
                registrar_log('error', 'auto_procesar', 
                            f"Baja confianza: {filename}", doc_id)
                
                print(f"📂 Movido a: {destino}")
                
                # Notificación
                notificar_macos(
                    "❌ Revisión Manual Necesaria",
                    f"{filename}\nConfianza: {confianza:.0%}",
                    'Basso'
                )
        
        except Exception as e:
            print(f"\n❌ ERROR PROCESANDO: {str(e)}")
            
            # Registrar error
            doc_id = registrar_documento(filepath, {}, 'error', 0.0)
            registrar_log('error', 'auto_procesar', 
                        f"Error: {str(e)}", doc_id)
            
            # Mover a REVISAR_MANUAL
            try:
                destino = mover_a_revision_manual(filepath)
                actualizar_estado_documento(doc_id, 'error', destino)
                print(f"📂 Movido a revisión manual: {destino}")
            except Exception as e2:
                print(f"❌ Error crítico: {e2}")
            
            # Notificación
            notificar_macos(
                "❌ Error de Procesamiento",
                f"{filename}",
                'Basso'
            )
        
        print(f"{'='*70}\n")

# ============================================
# MAIN
# ============================================

def main():
    print("\n" + "="*70)
    print("🤖 AUTO-PROCESADOR PRO - LexDocsPro LITE v2.0")
    print("="*70)
    print(f"📁 Monitoreando: {PENDIENTES_DIR}")
    print(f"📂 Destino: {EXPEDIENTES_DIR}")
    print(f"🗄️ Base de datos: {DB_PATH}")
    print(f"🌐 API: {API_URL}")
    print("\n⚙️ UMBRALES:")
    print(f"   ✅ Auto: ≥{UMBRAL_AUTO:.0%}")
    print(f"   ⚠️ Revisión: {UMBRAL_REVISION:.0%}-{UMBRAL_AUTO:.0%}")
    print(f"   ❌ Manual: <{UMBRAL_REVISION:.0%}")
    print("\n⏸️ Presiona Ctrl+C para detener")
    print("="*70 + "\n")
    
    # Inicializar BD
    init_database()
    registrar_log('info', 'sistema', 'Auto-procesador iniciado')
    
    # Crear carpetas si no existen
    os.makedirs(PENDIENTES_DIR, exist_ok=True)
    os.makedirs(EXPEDIENTES_DIR, exist_ok=True)
    
    # Verificar que Flask esté corriendo
    try:
        response = requests.get(f'{API_URL}/api/health', timeout=5)
        if response.status_code != 200:
            print("⚠️ ADVERTENCIA: Flask no responde correctamente")
            print("   Asegúrate de ejecutar: python run.py")
    except:
        print("❌ ERROR: No se puede conectar con Flask")
        print("   Ejecuta primero: python run.py")
        print("   Luego ejecuta: python auto_procesar.py")
        return
    
    # Iniciar monitor
    event_handler = DocumentHandler()
    observer = Observer()
    observer.schedule(event_handler, PENDIENTES_DIR, recursive=False)
    observer.start()
    
    print("✅ Monitor activo - Esperando documentos...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        registrar_log('info', 'sistema', 'Auto-procesador detenido')
        print("\n\n👋 Monitor detenido correctamente")
    
    observer.join()

if __name__ == '__main__':
    main()
