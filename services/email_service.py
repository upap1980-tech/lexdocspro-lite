import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Optional

class EmailService:
    """
    Servicio para envío de emails automatizados
    LexDocsPro LITE v2.2.0
    """
    
    def __init__(self):
        # Cargar configuración desde variables de entorno
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', f"LexDocsPro <{self.smtp_user}>")
        
        # Configurar Jinja2 para templates de email
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'email')
        if not os.path.exists(template_dir):
            os.makedirs(template_dir, exist_ok=True)
            
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def send_critical_notification(self, to_email: str, notification_data: Dict) -> bool:
        """
        Enviar email de alerta para notificaciones CRITICAL
        """
        try:
            subject = f"🚨 ALERTA CRÍTICA: Plazo LexNET Próximo ({notification_data.get('procedure_number', 'N/A')})"
            
            # Datos para el template
            context = {
                'notification': notification_data,
                'dashboard_url': os.getenv('DASHBOARD_URL', 'http://localhost:5001'),
                'current_year': datetime.now().year if 'datetime' in globals() else 2026
            }
            
            # Si no importamos datetime arriba
            from datetime import datetime
            context['current_year'] = datetime.now().year

            html_content = self.render_template('critical_notification.html', context)
            
            return self.send_email(to_email, subject, html_content)
            
        except Exception as e:
            print(f"❌ Error preparando email crítico: {str(e)}")
            return False

    def render_template(self, template_name: str, context: Dict) -> str:
        """Renderizar un template HTML de email"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            print(f"❌ Error renderizando template {template_name}: {str(e)}")
            # Fallback simple si el template falla
            return f"Alerta LexNET: {context.get('notification', {}).get('title', 'Sin título')}"

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Envío físico del email vía SMTP
        """
        if not self.smtp_user or not self.smtp_password:
            print("⚠️ SMTP no configurado (SMTP_USER/SMTP_PASSWORD faltantes)")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Añadir versión HTML
            part_html = MIMEText(html_content, 'html')
            msg.attach(part_html)

            # Conectar y enviar
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Upgrade a conexión segura
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                
            print(f"✅ Email enviado correctamente a {to_email}")
            return True

        except Exception as e:
            print(f"❌ Error enviando email: {str(e)}")
            return False
