# Checklist de Testeo Manual (Módulo por Módulo)

Fecha: 2026-02-06

## Pre-requisitos
- `./run.sh` ejecutándose
- Base de datos con datos demo (opcional): `python3 populate_test_data.py`
- Navegador abierto en `http://localhost:5001`

## Dashboard
- Ver KPIs (hoy / en revisión / errores / alertas) sin errores JS.
- Botón `Actualizar` recarga datos.
- Botón `Exportar PDF` abre descarga en pestaña nueva.
- Sección detalle muestra `stats-detailed` y `drill-down` sin error.

## Autoprocesos
- `Escanear` muestra estado actualizado.
- `Reset` reinicia estadísticas.
- Botones legacy (`Stats`, `Cola revisión`, `Procesados hoy`, `Clientes`, `Logs`, `Toggle`, `Watchdog`) responden 2xx.
- Vista de log muestra tabla de procesos o mensaje vacío controlado.

## IA Cascade
- `Refresh` carga stats.
- `Reset stats` responde OK.
- `Export` descarga JSON.

## OCR / PDF / Files
- Seleccionar archivo PDF en Files.
- `Run OCR` devuelve texto (o error controlado si archivo inválido).
- `OCR Upload` sube archivo desde UI y responde 2xx/4xx.
- `Preview Data` devuelve thumbnails demo.

## Documentos E2E (IA Agent)
- `Smart Analyze` acepta archivo PDF.
- `Propose Save` genera propuesta.
- `Confirm Save` guarda documento.
- `Load Saved` lista documentos guardados.
- `Signature Sign` usa certificado disponible (o devuelve 400 controlado).

## Email Alerts
- Guardar email.
- Enviar test email.
- Ver historial.

## Firma Digital
- `Status` responde OK.
- `Sign` con doc_id válido responde OK.

## Banking
- `Load` devuelve stats/transactions demo.

## Usuarios
- `Load` devuelve equipo.
- `Invitar` crea usuario demo.

## Analytics
- `Load` devuelve metrics.

## Expedientes / iCloud
- Listar clientes iCloud.
- Exportar análisis (si permitido por permisos del sistema).

## LexNET
- Upload de XML/PDF de prueba.
- Listar notificaciones con filtros.
- Marcar como leída.
- Analizar texto.
- `Urgentes legacy` y `Analizar plazo` responden 2xx.

## Config / Deploy
- `Load` config.
- `Save` config.
- `Deploy status` responde OK.

## Criterio de salida
- Sin errores JS fatales.
- Respuestas controladas (2xx o 4xx), no 500.
- Reporte `reports/forensic_module_audit.json` en `OK=15`.
