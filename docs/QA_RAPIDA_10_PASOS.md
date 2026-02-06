# QA Rápida (10 pasos)

Fecha: 2026-02-06

1. Abrir `http://localhost:5001` y comprobar que carga sin errores JS fatales.
2. Dashboard: KPIs visibles y botón `Exportar PDF` abre descarga.
3. Autoprocesos: `Actualizar` muestra estado y `Logs legacy` responde 2xx.
4. OCR: seleccionar PDF en Files y ejecutar `Run OCR`.
5. Documentos E2E: `Smart Analyze` + `Propose Save` responden 2xx/4xx controlado.
6. LexNET: `Upload` de XML/PDF y `Listar` notificaciones con filtros.
7. IA Cascade: `Refresh` stats y `Export` descarga JSON.
8. Firma: `Status` responde OK (si hay certificado, `Sign`).
9. Alerts: `Test Email` responde 2xx/4xx controlado.
10. Verificar `reports/forensic_module_audit.json` con `OK=15`.
