"""
Analizador de Notificaciones LexNET
Calcula plazos procesales y genera análisis automático
"""
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple

class LexNetAnalyzer:
    """Analizador de notificaciones LexNET"""
    
    # Festivos 2025-2026
    FESTIVOS_NAC_2025 = [
        "2025-01-01", "2025-01-06", "2025-04-17", "2025-04-18",
        "2025-05-01", "2025-08-15", "2025-10-12", "2025-11-01",
        "2025-12-06", "2025-12-08", "2025-12-25"
    ]
    
    FESTIVOS_NAC_2026 = [
        "2026-01-01", "2026-01-06", "2026-04-02", "2026-04-03",
        "2026-05-01", "2026-08-15", "2026-10-12", "2026-11-02",
        "2026-12-08", "2026-12-25"
    ]
    
    FESTIVOS_SC_PALMA = ["2025-05-03", "2025-06-30", "2026-05-03", "2026-06-30"]
    FESTIVOS_SC_TENER = ["2025-03-04", "2025-05-02", "2026-03-04", "2026-05-02"]
    FESTIVOS_CANARIAS = ["2025-05-30", "2026-05-30"]
    FESTIVOS_LA_PALMA = ["2025-08-05", "2026-08-05"]
    FESTIVOS_TENERIFE = ["2025-02-02", "2026-02-02"]
    
    # Periodo inhábil
    INHABILES = [
        ("2025-08-01", "2025-08-31"),
        ("2025-12-24", "2026-01-06"),
        ("2026-08-01", "2026-08-31"),
        ("2026-12-24", "2027-01-06")
    ]
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.festivos_todos = (
            self.FESTIVOS_NAC_2025 + self.FESTIVOS_NAC_2026 +
            self.FESTIVOS_SC_PALMA + self.FESTIVOS_SC_TENER +
            self.FESTIVOS_CANARIAS + self.FESTIVOS_LA_PALMA + 
            self.FESTIVOS_TENERIFE
        )
    
    def analizar_notificacion(self, textos: Dict[str, str], provider: str = 'ollama') -> str:
        """
        Analizar notificación LexNET completa
        
        Args:
            textos: {'resumen': str, 'caratula': str, 'principal': str, 'adjuntos': [str]}
            provider: Proveedor de IA
        """
        
        # 1. Extraer datos con IA
        datos = self._extraer_datos_ia(textos, provider)
        
        # 2. Calcular plazos si aplica
        if datos.get('plazo_dias'):
            datos['calculo_plazo'] = self._calcular_plazo(
                datos['fecha_notif'],
                datos['plazo_dias'],
                datos['sede']
            )
        
        # 3. Generar análisis formateado
        analisis = self._generar_analisis_texto(datos, textos)
        
        return analisis
    
    def _extraer_datos_ia(self, textos: Dict, provider: str) -> Dict:
        """Extraer datos usando IA"""
        
        prompt = f"""Analiza esta notificación LexNET y extrae EXACTAMENTE estos datos:

RESUMEN.pdf:
{textos.get('resumen', '')[:2000]}

CARATULA.pdf:
{textos.get('caratula', '')[:2000]}

DOCUMENTO PRINCIPAL:
{textos.get('principal', '')[:4000]}

EXTRAE (responde en formato JSON):
{{
  "numero_expediente": "Número/Año",
  "nig": "NIG completo",
  "jurisdiccion": "Civil/Penal/Contencioso/Social",
  "procedimiento": "Tipo de procedimiento",
  "organo": "Juzgado o Tribunal completo",
  "sede": "Ciudad (Santa Cruz de La Palma/Santa Cruz de Tenerife/Las Palmas)",
  "cliente": "NOMBRE COMPLETO del cliente/denunciado/demandante",
  "procurador": "Nombre del procurador o N/A",
  "letrado": "Victor Manuel Francisco Herrera",
  "contraria": "Nombre parte contraria o N/A",
  "fecha_notif": "DD/MM/YYYY HH:MM (buscar en RESUMEN: fecha ACEPTACIÓN por letrado)",
  "fecha_resol": "DD/MM/YYYY (fecha de la resolución del documento principal)",
  "tipo_resol": "AUTO/PROVIDENCIA/SENTENCIA/DECRETO/etc",
  "resumen_resol": "Resumen de 3-5 líneas de qué resuelve",
  "accion_requerida": "Qué debe hacer el letrado/cliente",
  "plazo_dias": número o null (si no hay plazo específico)
}}

IMPORTANTE:
- fecha_notif: Buscar "Fecha Generación" o similar en RESUMEN
- Si no encuentras algo, pon "N/A" o null
- plazo_dias: solo el número, sin texto"""

        result = self.ai_service.chat(
            prompt=prompt,
            provider=provider,
            mode='deep'
        )
        
        if not result['success']:
            return {'error': result.get('error')}
        
        # Parsear JSON de respuesta
        import json
        try:
            # Buscar JSON en la respuesta
            response_text = result['response']
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                datos = json.loads(json_match.group())
                return datos
            else:
                return {'error': 'No se pudo extraer JSON de la respuesta'}
        except Exception as e:
            return {'error': f'Error parseando JSON: {str(e)}'}
    
    def _calcular_plazo(self, fecha_notif_str: str, plazo_dias: int, sede: str) -> Dict:
        """Calcular plazo procesal"""
        
        try:
            # Parsear fecha notificación
            fecha_notif = datetime.strptime(fecha_notif_str.split()[0], '%d/%m/%Y')
            hora_notif = fecha_notif_str.split()[1] if len(fecha_notif_str.split()) > 1 else "00:00"
            hora_decimal = int(hora_notif.split(':')[0]) + int(hora_notif.split(':')[1])/60
            
            # Calcular dies a quo
            if hora_decimal >= 15:
                dies_a_quo = self._siguiente_habil(fecha_notif + timedelta(days=2))
            else:
                dies_a_quo = self._siguiente_habil(fecha_notif + timedelta(days=1))
            
            # Contar días hábiles
            detalle = []
            dias_contados = 0
            fecha_actual = dies_a_quo
            
            while dias_contados < plazo_dias:
                if self._es_habil(fecha_actual, sede):
                    dias_contados += 1
                    detalle.append(f"{fecha_actual.strftime('%d/%m')} ✅")
                else:
                    detalle.append(f"{fecha_actual.strftime('%d/%m')} ❌")
                
                fecha_actual += timedelta(days=1)
            
            dies_ad_quem = fecha_actual - timedelta(days=1)
            dia_gracia = self._siguiente_habil(dies_ad_quem + timedelta(days=1))
            
            return {
                'dies_a_quo': dies_a_quo.strftime('%d/%m/%Y'),
                'dies_ad_quem': dies_ad_quem.strftime('%d/%m/%Y') + ' 24:00h',
                'dia_gracia': dia_gracia.strftime('%d/%m/%Y') + ' 15:00h',
                'detalle': ' | '.join(detalle),
                'dias_naturales': (dies_ad_quem - dies_a_quo).days + 1
            }
            
        except Exception as e:
            return {'error': f'Error calculando plazo: {str(e)}'}
    
    def _es_habil(self, fecha: datetime, sede: str) -> bool:
        """Verificar si fecha es hábil"""
        
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        # Sábado o domingo
        if fecha.weekday() >= 5:
            return False
        
        # Periodo inhábil
        for inicio, fin in self.INHABILES:
            if inicio <= fecha_str <= fin:
                return False
        
        # Festivos nacionales
        if fecha_str in self.FESTIVOS_NAC_2025 + self.FESTIVOS_NAC_2026:
            return False
        
        # Festivos autonómicos
        if fecha_str in self.FESTIVOS_CANARIAS:
            return False
        
        # Festivos locales según sede
        if 'PALMA' in sede.upper():
            if fecha_str in self.FESTIVOS_SC_PALMA + self.FESTIVOS_LA_PALMA:
                return False
        
        if 'TENERIFE' in sede.upper():
            if fecha_str in self.FESTIVOS_SC_TENER + self.FESTIVOS_TENERIFE:
                return False
        
        return True
    
    def _siguiente_habil(self, fecha: datetime) -> datetime:
        """Obtener siguiente día hábil"""
        while not self._es_habil(fecha, ""):
            fecha += timedelta(days=1)
        return fecha
    
    def _generar_analisis_texto(self, datos: Dict, textos: Dict) -> str:
        """Generar archivo de texto con análisis"""
        
        analisis = f"""================================================================================
ANÁLISIS LEXNET - EXPEDIENTE {datos.get('numero_expediente', 'N/A')}
================================================================================

1. EXPEDIENTE
================================================================================
Nº Expediente: {datos.get('numero_expediente', 'N/A')}
NIG: {datos.get('nig', 'N/A')}
Jurisdicción: {datos.get('jurisdiccion', 'N/A')}
Procedimiento: {datos.get('procedimiento', 'N/A')}
Órgano: {datos.get('organo', 'N/A')}

2. PARTES
================================================================================
Cliente/Interviniente: {datos.get('cliente', 'N/A')}
Procurador: {datos.get('procurador', 'N/A')}
Letrado: {datos.get('letrado', 'Victor Manuel Francisco Herrera')}
Parte Contraria: {datos.get('contraria', 'N/A')}

3. FECHAS
================================================================================
📩 NOTIF: {datos.get('fecha_notif', 'N/A')}
📄 RESOL: {datos.get('fecha_resol', 'N/A')}
DIES A QUO: {datos.get('calculo_plazo', {}).get('dies_a_quo', 'N/A')}

4. RESUMEN
================================================================================
Tipo Resolución: {datos.get('tipo_resol', 'N/A')}

Síntesis:
{datos.get('resumen_resol', 'N/A')}

Acción:
{datos.get('accion_requerida', 'N/A')}

5. PLAZO
================================================================================
Sede: {datos.get('organo', 'N/A')}
Notif: {datos.get('fecha_notif', 'N/A')}
Dies a quo: {datos.get('calculo_plazo', {}).get('dies_a_quo', 'N/A')}

Plazo: {datos.get('plazo_dias', 'Sin plazo específico')} días hábiles

Festivos 2025-2026:
  - Nacionales: 1,6Ene | 17,18Abr | 1May | 15Ago | 12Oct | 1Nov | 6,8,25Dic (2025)
                1,6Ene | 2,3Abr | 1May | 15Ago | 12Oct | 2Nov | 8,25Dic (2026)
  - SC PALMA: 3May, 30Jun
  - Inhábil: 1-31 Ago, 24 Dic - 6 Ene

Detalle cómputo hábil:
{datos.get('calculo_plazo', {}).get('detalle', 'N/A')}

Dies ad quem: {datos.get('calculo_plazo', {}).get('dies_ad_quem', 'N/A')}
Gracia (135.5 LEC): {datos.get('calculo_plazo', {}).get('dia_gracia', 'N/A')}

6. TABLA
================================================================================
Fecha Res | Expediente | Cliente | Procurador/Letrado | Actuación | Plazo | Vencimiento | Día Gracia
{datos.get('fecha_resol', 'N/A')} | {datos.get('numero_expediente', 'N/A')} | {datos.get('cliente', 'N/A')} | {datos.get('procurador', 'N/A')} / Victor M.F. Herrera | {datos.get('tipo_resol', 'N/A')} | {datos.get('plazo_dias', 'N/A')} días | {datos.get('calculo_plazo', {}).get('dies_ad_quem', 'N/A').split()[0] if datos.get('calculo_plazo') else 'N/A'} | {datos.get('calculo_plazo', {}).get('dia_gracia', 'N/A').split()[0] if datos.get('calculo_plazo') else 'N/A'}

7. DOCUMENTACIÓN RENOMBRADA
================================================================================
Principal:
  {self._generar_nombre_archivo(datos, 'principal')}

Acuse:
  {self._generar_nombre_archivo(datos, 'acuse')}

Carátula:
  Caratula.pdf

8. DESTINO
================================================================================
Ruta primaria: /Users/victormfrancisco/Library/Mobile Documents/com~apple~CloudDocs/EXPEDIENTES/{datetime.now().year}/{datos.get('cliente', 'CLIENTE')}/

Si no existe: Crear en ruta primaria

================================================================================
Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Letrado: Victor Manuel Francisco Herrera
Colegio: Ilustre Colegio de Abogados de Santa Cruz de La Palma
================================================================================
"""
        return analisis
    
    def _generar_nombre_archivo(self, datos: Dict, tipo: str) -> str:
        """Generar nombre de archivo según convención"""
        
        fecha_resol = datos.get('fecha_resol', 'N/A')
        if fecha_resol != 'N/A':
            try:
                fecha_obj = datetime.strptime(fecha_resol, '%d/%m/%Y')
                fecha_formato = fecha_obj.strftime('%Y-%m-%d')
            except:
                fecha_formato = fecha_resol
        else:
            fecha_formato = datetime.now().strftime('%Y-%m-%d')
        
        tipo_resol = datos.get('tipo_resol', 'DOC')
        resumen_breve = datos.get('resumen_resol', '')[:30].replace('\n', ' ').strip()
        
        if tipo == 'acuse':
            return f"{fecha_formato} Acuse {tipo_resol} {resumen_breve}.pdf"
        else:
            return f"{fecha_formato} {tipo_resol} {resumen_breve}.pdf"
