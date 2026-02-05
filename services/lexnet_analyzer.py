from config import FESTIVOS_CANARIAS_2026
from datetime import datetime, timedelta
try:
    import holidays
except ImportError:
    holidays = None

class LexNetAnalyzer:
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.es_holidays = holidays.ES(years=2026) if holidays else None
        self.ca_holidays = FESTIVOS_CANARIAS_2026

    def calcular_plazo(self, fecha_recepcion, dias_habiles):
        """Calcula fecha exacta dies ad quem con festivos"""
        fecha = datetime.strptime(fecha_recepcion, '%Y-%m-%d').date()
        dias_contados = 0
        while dias_contados < dias_habiles:
            fecha += timedelta(days=1)
            if fecha.weekday() < 5 and str(fecha) not in self.ca_holidays:  # L-V y no festivo
                dias_contados += 1
        return fecha.strftime('%d/%m/%Y')

    def analizar_notificacion(self, textos, provider='ollama'):
        prompt = (
            "Analiza esta notificación LexNET y extrae: "
            "tipo_documento, cliente, numero_expediente, fecha_recepcion, plazo_respuesta_dias. "
            "Devuelve JSON."
        )
        text_blob = "\n\n".join(
            f"[{k.upper()}]\n{v}" for k, v in (textos or {}).items() if v
        )

        analisis = self.ai_service.consultar(
            text_blob,
            prompt,
            provider=provider,
            mode='standard'
        )
        # Ejemplo plazos comunes LEC
        if isinstance(analisis, str) and 'demanda' in analisis.lower():
            plazo_final = self.calcular_plazo('2026-02-04', 20)  # Art. 404 LEC
            analisis += f"\n⚠️ **PLAZO CRÍTICO**: 20 días hábiles hasta {plazo_final}"
        return analisis
