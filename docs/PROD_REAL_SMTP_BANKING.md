# Migracion minima segura: Email SMTP + Banking real

## Objetivo
Pasar de servicios simulados a servicios reales sin romper endpoints existentes.

## Variables exactas (.env)

### Email SMTP
```env
ALERT_EMAIL=admin@lexdocs.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASS=change-me
SMTP_FROM=LexDocsPro <noreply@example.com>
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT=20
```

### Banking (GoCardless/Nordigen)
```env
BANKING_PROVIDER=gocardless
BANKING_BASE_URL=https://bankaccountdata.gocardless.com/api/v2
BANKING_GOCARDLESS_SECRET_ID=
BANKING_GOCARDLESS_SECRET_KEY=
BANKING_COUNTRY=ES
BANKING_ACCOUNT_IDS=acc_id_1,acc_id_2
BANKING_TIMEOUT=20
```

## Comportamiento esperado

1. Email:
- `/api/alerts/test-email` envia SMTP real.
- Si falta config SMTP, devuelve `503` (sin 500).

2. Banking:
- `/api/banking/stats` usa proveedor real.
- `/api/banking/institutions` consulta instituciones reales.
- `/api/banking/transactions` consulta movimientos reales.
- Si falta config bancaria, devuelve `503` (sin 500).

## Validacion rapida

```bash
./start_produccion.sh
curl -s http://localhost:5002/api/health
curl -s -X POST http://localhost:5002/api/alerts/test-email -H 'Content-Type: application/json' -d '{"to_email":"tu@email.com"}'
curl -s http://localhost:5002/api/banking/institutions
curl -s http://localhost:5002/api/banking/transactions
```

## Rollback seguro

1. Vaciar variables SMTP y Banking en `.env`.
2. Reiniciar backend.
3. Endpoints pasaran a `503` controlado en lugar de 500.
