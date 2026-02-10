"""
Email Service - SMTP real with safe fallback behavior.
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "").strip()
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "").strip()
        self.smtp_pass = os.getenv("SMTP_PASS", "").strip()
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user or "noreply@lexdocs.local").strip()
        self.smtp_use_tls = _as_bool(os.getenv("SMTP_USE_TLS", "true"), True)
        self.smtp_use_ssl = _as_bool(os.getenv("SMTP_USE_SSL", "false"), False)
        self.smtp_timeout = int(os.getenv("SMTP_TIMEOUT", "20"))
        self.default_to = os.getenv("ALERT_EMAIL", self.smtp_user or "admin@lexdocs.com").strip()

    def _validate_config(self) -> tuple[bool, str]:
        if not self.smtp_host:
            return False, "SMTP_HOST no configurado"
        if not self.smtp_port:
            return False, "SMTP_PORT no configurado"
        if not self.smtp_user:
            return False, "SMTP_USER no configurado"
        if not self.smtp_pass:
            return False, "SMTP_PASS no configurado"
        return True, ""

    def send_alert(self, subject, body, to_email=None):
        """Enviar email real via SMTP. Returns True/False."""
        ok, err = self._validate_config()
        if not ok:
            print(f"❌ EmailService: configuración SMTP incompleta ({err})")
            return False

        recipient = (to_email or self.default_to).strip()
        if not recipient:
            print("❌ EmailService: destinatario vacío")
            return False

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.smtp_from
        msg["To"] = recipient
        msg.set_content(body)

        try:
            if self.smtp_use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=self.smtp_timeout) as smtp:
                    smtp.login(self.smtp_user, self.smtp_pass)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.smtp_timeout) as smtp:
                    smtp.ehlo()
                    if self.smtp_use_tls:
                        smtp.starttls()
                        smtp.ehlo()
                    smtp.login(self.smtp_user, self.smtp_pass)
                    smtp.send_message(msg)
            print(f"✅ Email enviado a {recipient}")
            return True
        except Exception as e:
            print(f"❌ Error enviando email SMTP: {e}")
            return False
