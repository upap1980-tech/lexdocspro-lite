import os
from datetime import datetime

class DecisionEngine:
    def __init__(self):
        pass

    def construir_ruta_destino(self, analisis: dict, base_dir: str):
        """
        Construye la ruta destino a partir del análisis:
        - cliente_codigo
        - tipo_documento
        - fecha_documento
        - archivo_original
        """
        cliente = analisis.get("cliente_codigo") or "SIN_CLIENTE"
        tipo = analisis.get("tipo_documento") or "SIN_TIPO"
        fecha_str = analisis.get("fecha_documento") or datetime.now().strftime("%Y%m%d")
        nombre = analisis.get("archivo_original") or "documento.pdf"

        # Estructura: BASE_DIR/cliente/tipo/AAAA/MM/
        ano = fecha_str[:4]
        mes = fecha_str[4:6] if len(fecha_str) >= 6 else "01"

        carpeta_cliente = os.path.join(base_dir, cliente)
        carpeta_tipo = os.path.join(carpeta_cliente, tipo)
        carpeta_fecha = os.path.join(carpeta_tipo, f"{ano}_{mes}")
        os.makedirs(carpeta_fecha, exist_ok=True)

        ruta_completa = os.path.join(carpeta_fecha, nombre)

        return {
            "carpeta_cliente": carpeta_cliente,
            "carpeta_tipo": carpeta_tipo,
            "carpeta_fecha": carpeta_fecha,
            "ruta_completa": ruta_completa,
        }

    def ejecutar_accion(self, accion: str, archivo_origen: str, destino: dict, carpeta_pendientes: str):
        """
        Mueve el archivo desde origen a la ruta_completa indicada en destino.
        """
        from shutil import move

        ruta_destino = destino["ruta_completa"]
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
        move(archivo_origen, ruta_destino)
        return True
