"""
LexNET Notifications Service
Parseo de archivos LexNET, detección de plazos urgentes y gestión de alertas
"""

from datetime import datetime, timedelta
import re
import PyPDF2
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional


class LexNetNotifications:
    """Servicio para gestionar notificaciones LexNET con alertas de urgencia"""
    
    def __init__(self, db_manager=None, ai_agent=None):
        self.db = db_manager
        self.ai_agent = ai_agent
        
        # Umbrales de urgencia en horas
        self.CRITICAL_HOURS = 24
        self.URGENT_HOURS = 48
        self.WARNING_HOURS = 72
        
        # Plazos legales comunes (en días)
        self.legal_deadlines = {
            'apelacion': 20,
            'reposicion': 5,
            'oposicion': 10,
            'alegaciones': 10,
            'contestacion': 20,
            'recurso': 20,
            'default': 10
        }
    
    def parse_lexnet_file(self, file_path: str) -> Dict:
        """
        Parsear archivo LexNET (PDF o XML) y extraer información relevante
        
        Returns:
            {
                'success': bool,
                'notification_data': {
                    'title': str,
                    'body': str,
                    'notification_date': str,
                    'deadline': str,
                    'procedure_number': str,
                    'court': str,
                    'urgency': str,  # 'CRITICAL', 'URGENT', 'WARNING', 'NORMAL'
                    'days_left': int
                }
            }
        """
        try:
            file_ext = file_path.lower().split('.')[-1]
            
            if file_ext == 'pdf':
                return self._parse_pdf(file_path)
            elif file_ext == 'xml':
                return self._parse_xml(file_path)
            else:
                return {'success': False, 'error': f'Formato no soportado: {file_ext}'}
        
        except Exception as e:
            print(f"❌ Error parseando archivo LexNET: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_pdf(self, file_path: str) -> Dict:
        """Parsear PDF de notificación LexNET"""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ''
                
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            return self._extract_notification_data(text, 'pdf')
        
        except Exception as e:
            return {'success': False, 'error': f'Error leyendo PDF: {str(e)}'}
    
    def _parse_xml(self, file_path: str) -> Dict:
        """Parsear XML de notificación LexNET"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extraer campos comunes de XML LexNET
            notification_data = {
                'title': self._get_xml_text(root, './/Asunto') or 'Notificación LexNET',
                'procedure_number': self._get_xml_text(root, './/NumProcedimiento') or '',
                'court': self._get_xml_text(root, './/Organo') or '',
                'notification_date': self._get_xml_text(root, './/FechaNotificacion') or '',
                'body': self._get_xml_text(root, './/Contenido') or ''
            }
            
            # Determinar deadline y urgencia
            self._calculate_deadline_and_urgency(notification_data)
            
            return {
                'success': True,
                'notification_data': notification_data
            }
        
        except Exception as e:
            return {'success': False, 'error': f'Error parseando XML: {str(e)}'}
    
    def _get_xml_text(self, root, xpath: str) -> Optional[str]:
        """Helper para extraer texto de XML"""
        element = root.find(xpath)
        return element.text if element is not None else None
    
    def _extract_notification_data(self, text: str, source_type: str) -> Dict:
        """Extraer datos estructurados del texto de la notificación"""
        
        notification_data = {
            'title': 'Notificación LexNET',
            'body': text[:500],  # Primeros 500 caracteres
            'procedure_number': '',
            'court': '',
            'notification_date': '',
            'deadline': '',
            'urgency': 'NORMAL',
            'days_left': 0
        }
        
        # Extraer número de procedimiento
        proc_match = re.search(r'(?:Procedimiento|Proc\.|Nº)\s*:?\s*(\d+/\d{4})', text, re.IGNORECASE)
        if proc_match:
            notification_data['procedure_number'] = proc_match.group(1)
        
        # Extraer juzgado/tribunal
        court_match = re.search(r'(Juzgado[^\.]+|Tribunal[^\.]+)', text, re.IGNORECASE)
        if court_match:
            notification_data['court'] = court_match.group(1).strip()
        
        # Extraer fecha de notificación
        date_patterns = [
            r'Fecha de notificación:\s*(\d{2}/\d{2}/\d{4})',
            r'Notificado el:\s*(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                notification_data['notification_date'] = date_match.group(1)
                break
        
        # Si no hay fecha, usar fecha actual
        if not notification_data['notification_date']:
            notification_data['notification_date'] = datetime.now().strftime('%d/%m/%Y')
        
        # Determinar tipo de notificación y plazo
        notification_type = self._detect_notification_type(text)
        
        # Calcular deadline
        self._calculate_deadline_and_urgency(notification_data, notification_type)
        
        # Mejorar título si es posible
        if notification_type != 'default':
            notification_data['title'] = f'Notificación: {notification_type.upper()}'
        
        return {
            'success': True,
            'notification_data': notification_data
        }
    
    def _detect_notification_type(self, text: str) -> str:
        """Detectar tipo de notificación para determinar plazo legal"""
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['sentencia', 'fallo']):
            return 'apelacion'  # 20 días
        elif any(word in text_lower for word in ['auto', 'providencia']):
            return 'reposicion'  # 5 días
        elif 'oposición' in text_lower or 'oposicion' in text_lower:
            return 'oposicion'  # 10 días
        elif 'alegaciones' in text_lower or 'alegación' in text_lower:
            return 'alegaciones'  # 10 días
        elif 'demanda' in text_lower:
            return 'contestacion'  # 20 días
        elif 'recurso' in text_lower:
            return 'recurso'  # 20 días
        else:
            return 'default'  # 10 días
    
    def _calculate_deadline_and_urgency(self, notification_data: Dict, notification_type: str = 'default'):
        """Calcular deadline y nivel de urgencia basado en la fecha de notificación"""
        
        try:
            # Parsear fecha de notificación
            if notification_data.get('notification_date'):
                if '/' in notification_data['notification_date']:
                    # Formato DD/MM/YYYY
                    date_parts = notification_data['notification_date'].split('/')
                    notification_date = datetime(
                        int(date_parts[2]), 
                        int(date_parts[1]), 
                        int(date_parts[0])
                    )
                else:
                    # Formato ISO
                    notification_date = datetime.fromisoformat(notification_data['notification_date'])
            else:
                notification_date = datetime.now()
            
            # Obtener plazo legal
            deadline_days = self.legal_deadlines.get(notification_type, self.legal_deadlines['default'])
            
            # Calcular deadline
            deadline = notification_date + timedelta(days=deadline_days)
            notification_data['deadline'] = deadline.strftime('%Y-%m-%d')
            
            # Calcular días restantes
            now = datetime.now()
            days_left = (deadline - now).days
            notification_data['days_left'] = max(0, days_left)
            
            # Determinar urgencia
            hours_left = (deadline - now).total_seconds() / 3600
            
            if hours_left <= self.CRITICAL_HOURS:
                notification_data['urgency'] = 'CRITICAL'
            elif hours_left <= self.URGENT_HOURS:
                notification_data['urgency'] = 'URGENT'
            elif hours_left <= self.WARNING_HOURS:
                notification_data['urgency'] = 'WARNING'
            else:
                notification_data['urgency'] = 'NORMAL'
        
        except Exception as e:
            print(f"⚠️ Error calculando deadline: {e}")
            # Valores por defecto en caso de error
            notification_data['deadline'] = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
            notification_data['days_left'] = 10
            notification_data['urgency'] = 'NORMAL'
    
    def save_notification(self, notification_data: Dict, user_id: int) -> int:
        """Guardar notificación en la base de datos"""
        
        if not self.db:
            raise Exception("DatabaseManager no inicializado")
        
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("""
                INSERT INTO notifications (
                    user_id, type, title, body, 
                    deadline, urgency, procedure_number, court,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                'lexnet',
                notification_data.get('title', 'Notificación LexNET'),
                notification_data.get('body', ''),
                notification_data.get('deadline'),
                notification_data.get('urgency', 'NORMAL'),
                notification_data.get('procedure_number', ''),
                notification_data.get('court', ''),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            notification_id = cursor.lastrowid
            conn.close()
            
            # 1. Disparar email si es crítico
            self._trigger_email_if_critical(notification_data, user_id)
            
            # 2. Trigger AI AGENT Auto-Drafting (v3.0.0 PRO)
            self._trigger_ai_autodraft(notification_data, user_id)
            
            return notification_id
        
        except Exception as e:
            print(f"❌ Error guardando notificación: {e}")
            raise

    def _trigger_ai_autodraft(self, notification_data, user_id):
        """Disparar generación autónoma de borrador basado en la notificación"""
        if not self.ai_agent:
            return

        proc_num = notification_data.get('procedure_number')
        if not proc_num:
            return

        print(f"🤖 AI AGENT: Detectada notificación para autos {proc_num}. Generando borrador preventivo...")
        
        # Determinar tipo de documento a generar basado en la notificación
        doc_type = 'contestacion_demanda' if 'demanda' in notification_data.get('title', '').lower() else 'escrito_alegaciones'
        
        try:
            # En v3.0 el agente hereda el contexto del expediente si existe
            # (El agente buscará el expediente por el número de procedimiento en su lógica interna o BD)
            draft = self.ai_agent.generate_draft(
                expediente_id=proc_num, 
                doc_type=doc_type,
                user_instructions=f"Generar respuesta técnica a la notificación: {notification_data.get('title')}"
            )
            
            # Guardar el borrador en logs o como documento pendiente
            # self.db.registrar_borrador_agente(...)
            print(f"✅ AI AGENT: Borrador '{doc_type}' preparado para revisión.")
            
        except Exception as e:
            print(f"⚠️ AI AGENT: No se pudo generar borrador automático: {e}")

    def _trigger_email_if_critical(self, notification_data, user_id):
        """Disparar email si la urgencia es CRÍTICA"""
        if notification_data.get('urgency') == 'CRITICAL':
            try:
                # Obtener email del usuario
                conn = self.db.get_connection()
                user_row = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
                conn.close()
                
                if user_row and user_row[0]:
                    user_email = user_row[0]
                    from services.email_service import EmailService
                    email_service = EmailService()
                    
                    print(f"📧 Disparando email de alerta crítica a {user_email}...")
                    email_service.send_critical_notification(user_email, notification_data)
                else:
                    print(f"⚠️ No se encontró email para el usuario ID {user_id}")
            except Exception as e:
                print(f"❌ Error en trigger de email: {str(e)}")
    
    def get_urgent_count(self, user_id: Optional[int] = None) -> int:
        """Contar notificaciones urgentes (CRITICAL o URGENT) no leídas"""
        
        if not self.db:
            return 0
        
        try:
            conn = self.db.get_connection()
            query = """
                SELECT COUNT(*) FROM notifications 
                WHERE read = 0 
                AND urgency IN ('CRITICAL', 'URGENT')
            """
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            result = conn.execute(query, params).fetchone()
            conn.close()
            return result[0] if result else 0
        
        except Exception as e:
            print(f"❌ Error contando notificaciones urgentes: {e}")
            return 0
    
    def get_notifications(self, user_id: Optional[int] = None, 
                         unread_only: bool = False,
                         urgency: Optional[str] = None,
                         limit: int = 50) -> List[Dict]:
        """Obtener listado de notificaciones"""
        
        if not self.db:
            return []
        
        try:
            query = "SELECT * FROM notifications WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if unread_only:
                query += " AND read = 0"
            
            if urgency:
                query += " AND urgency = ?"
                params.append(urgency)
            
            query += " ORDER BY deadline ASC, created_at DESC LIMIT ?"
            params.append(limit)
            
            conn = self.db.get_connection()
            cursor = conn.execute(query, params)
            
            notifications = []
            for row in cursor.fetchall():
                notifications.append({
                    'id': row[0],
                    'user_id': row[1],
                    'type': row[2],
                    'title': row[3],
                    'body': row[4],
                    'deadline': row[5],
                    'urgency': row[6],
                    'procedure_number': row[7],
                    'court': row[8],
                    'read': bool(row[9]),
                    'created_at': row[10]
                })
            conn.close()
            return notifications
        
        except Exception as e:
            print(f"❌ Error obteniendo notificaciones: {e}")
            return []
    
    def mark_as_read(self, notification_id: int, user_id: Optional[int] = None) -> bool:
        """Marcar notificación como leída"""
        
        if not self.db:
            return False
        
        try:
            conn = self.db.get_connection()
            conn.execute(query, params)
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            print(f"❌ Error marcando notificación como leída: {e}")
            return False
