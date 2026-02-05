"""
Email Service - Envío de alertas por email
"""

class EmailService:
    def send_alert(self, subject, body, to_email=None):
        """Enviar email de alerta"""
        print(f"📧 EMAIL ALERT (simulado)")
        print(f"   To: {to_email or 'admin@lexdocs.com'}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body[:100]}...")
        return True

