from datetime import datetime, timedelta

class DeadlineSkill:
    """
    Skill especializado en cálculo de plazos procesales (LEC)
    Artículos 133, 135, 151, 182 LEC.
    """
    
    # Festivos fijos (simplificado)
    FESTIVOS_FIJOS = ["01-01", "01-06", "05-01", "08-15", "10-12", "11-01", "12-06", "12-08", "12-25"]
    
    def calculate(self, fecha_notificacion: datetime, dias: int, tipo="habil"):
        """
        Calcula el vencimiento de un plazo.
        
        Args:
            fecha_notificacion: datetime del acto de comunicación.
            dias: int, duración del plazo.
            tipo: "habil" (default) o "natural".
            
        Returns:
            dict: {
                'dies_a_quo': datetime,
                'dies_ad_quem': datetime,
                'dia_gracia': datetime,
                'msg': str
            }
        """
        # Dies a quo: Día siguiente hábil (Art 133.1 LEC)
        # Si notificación fue > 15:00, se cuenta desde el día siguiente (Art 151.2 LEC fictamente)
        # PERO para el cómputo, el dia siguiente a la notificacion real es el primero.
        # Simplificación: Asumimos fecha_notificacion es efectiva.
        
        dies_a_quo = fecha_notificacion + timedelta(days=1)
        while not self._es_habil(dies_a_quo):
            dies_a_quo += timedelta(days=1)
            
        current_date = dies_a_quo
        dias_contados = 0
        
        if tipo == "natural":
            # Cómputo natural (ej. meses/años en sustantivo, pero LEC suele ser hábiles para días)
            # Si dias es meses, la lógica cambia. Asumimos días.
            final_date = current_date + timedelta(days=dias)
            # Si vence en inhábil, se prorroga al siguiente hábil (Art 133.4)
            while not self._es_habil(final_date):
                 final_date += timedelta(days=1)
            dies_ad_quem = final_date
        else:
            # Cómputo hábil (Art 133.2 LEC)
            while dias_contados < dias:
                if self._es_habil(current_date):
                    dias_contados += 1
                if dias_contados < dias:
                    current_date += timedelta(days=1)
            dies_ad_quem = current_date
            
        # Dia de Gracia (Art 151 LEC - hasta las 15:00 del día siguiente hábil)
        dia_gracia = dies_ad_quem + timedelta(days=1)
        while not self._es_habil(dia_gracia):
            dia_gracia += timedelta(days=1)
            
        return {
            'fecha_notificacion': fecha_notificacion.strftime("%d/%m/%Y"),
            'plazo_dias': dias,
            'dies_a_quo': dies_a_quo.strftime("%d/%m/%Y"),
            'dies_ad_quem': dies_ad_quem.strftime("%d/%m/%Y"),
            'dia_gracia': dia_gracia.strftime("%d/%m/%Y"),
            'vencimiento_desc': f"Vence el {dies_ad_quem.strftime('%d/%m/%Y')} (Gracia: {dia_gracia.strftime('%d/%m')} hasta 15:00)"
        }

    def _es_habil(self, date: datetime):
        # Sábados y Domingos inhábiles (Art 182 LEC)
        if date.weekday() >= 5: # 5=Sat, 6=Sun
            return False
            
        # Agosto inhábil (Art 183 LEC) - Salvo excepciones penales/urgentes
        if date.month == 8:
            return False
            
        # Festivos fijos
        md = date.strftime("%m-%d")
        if md in self.FESTIVOS_FIJOS:
            return False
            
        # 24 y 31 dic (aunque no sean festivos, suelen ser inhábiles a efectos prácticos o reducidos)
        # La LOPJ declara inhábiles 24 y 31 dic
        if md in ["12-24", "12-31"]:
            return False
            
        return True
