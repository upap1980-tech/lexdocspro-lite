#!/bin/bash
# Test de Notificaciones por Email (v2.2.0)

echo "============================================"
echo "📧 TEST SUITE - Email Notifications"
echo "============================================"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar variables de entorno
if [ -f .env ]; then
    source .env
fi

if [ -z "$SMTP_USER" ]; then
    echo -e "${RED}❌ ERROR: SMTP_USER no definido en .env${NC}"
    exit 1
fi

echo "📋 Probando configuración SMTP..."
python3 << EOF
import os
from services.email_service import EmailService
from dotenv import load_dotenv

load_dotenv()
service = EmailService()

# Mock de notificación crítica
test_notif = {
    'title': 'TEST CRITICAL NOTIFICATION',
    'procedure_number': '999/2026',
    'court': 'Juzgado de Test',
    'deadline': '2026-02-05',
    'urgency': 'CRITICAL',
    'created_at': '2026-02-04 10:00:00'
}

print(f"Enviando email de prueba a {os.getenv('SMTP_USER')}...")
success = service.send_critical_notification(os.getenv('SMTP_USER'), test_notif)

if success:
    print("✅ PASS: Email enviado (verifica tu bandeja de entrada)")
else:
    print("❌ FAIL: Error enviando email")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 TEST DE EMAIL COMPLETADO CON ÉXITO${NC}"
else
    echo -e "${RED}❌ EL TEST DE EMAIL FALLÓ${NC}"
    exit 1
fi
