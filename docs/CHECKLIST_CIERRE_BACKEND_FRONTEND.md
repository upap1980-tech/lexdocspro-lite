# Checklist Ejecutable Backend → Frontend

Estados: `OK`, `PARCIAL`, `SIN CORRESPONDENCIA`.

## Resumen

| Fase | OK | PARCIAL | SIN CORRESPONDENCIA |
|---|---:|---:|---:|
| P0 | 21 | 0 | 0 |
| P1 | 39 | 0 | 0 |
| P2 | 26 | 0 | 0 |

## Endpoint Por Endpoint

| Fase | Módulo | Endpoint | Método | Estado | Owner | Archivo | Acción |
|---|---|---|---|---|---|---|---|
| P0 | AutoProcessor v2 | `/api/autoprocessor/log` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | AutoProcessor v2 | `/api/autoprocessor/reset` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | AutoProcessor v2 | `/api/autoprocessor/scan` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | AutoProcessor v2 | `/api/autoprocessor/start` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | AutoProcessor v2 | `/api/autoprocessor/status` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | AutoProcessor v2 | `/api/autoprocessor/stop` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | Dashboard | `/api/dashboard/drill-down/by-date/<date_str>` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | Dashboard | `/api/dashboard/export-pdf` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | Dashboard | `/api/dashboard/stats` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | Dashboard | `/api/dashboard/stats-detailed` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/health` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/providers` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/providers-public` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/query` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/reset-stats` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/stats` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/stats-public` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/status` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/test` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/toggle-provider` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P0 | IA Cascade | `/api/ia-cascade/update-key` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesador/aprobar/<int:doc_id>` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesador/clientes` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesador/cola-revision` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesador/documento/<int:doc_id>` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesador/pdf/<int:doc_id>` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesador/procesados-hoy` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesador/rechazar/<int:doc_id>` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesador/stats` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesos/logs` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/autoprocesos/toggle` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | AutoProcesador legacy | `/api/watchdog-status` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/confirm-save` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/path-options` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/preview` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/propose-save` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/save-organized` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/saved` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/saved/<int:doc_id>` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/smart-analyze` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/thumbnails` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/document/types` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/documents/generate` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | Documentos | `/api/documents/templates` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | LexNET | `/api/lexnet-urgent` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | LexNET | `/api/lexnet/analizar-plazo` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | LexNET | `/api/lexnet/analyze` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | LexNET | `/api/lexnet/notifications` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | LexNET | `/api/lexnet/notifications/<int:notification_id>/read` | `PATCH` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | LexNET | `/api/lexnet/upload-notification` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | LexNET | `/api/lexnet/urgent-count` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | OCR/PDF/Files | `/api/files` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | OCR/PDF/Files | `/api/ocr` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | OCR/PDF/Files | `/api/ocr/upload` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | OCR/PDF/Files | `/api/pdf/<path:filepath>` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | OCR/PDF/Files | `/api/pdf/preview-data` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | iCloud | `/api/icloud/clients` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | iCloud | `/api/icloud/export` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | iCloud | `/api/icloud/export-analysis` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P1 | iCloud | `/api/icloud/status` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Alertas | `/api/alerts/config` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Alertas | `/api/alerts/history` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Alertas | `/api/alerts/test-email` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Analytics/Expedientes | `/api/analytics/detailed` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Analytics/Expedientes | `/api/expedientes/listar` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Banking | `/api/banking/institutions` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Banking | `/api/banking/stats` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Banking | `/api/banking/transactions` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Business skills | `/api/business/jurisdictions` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Business skills | `/api/business/strategy` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Business skills | `/api/business/templates` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Config/Deploy | `/api/config/get` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Config/Deploy | `/api/config/save` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Config/Deploy | `/api/deploy/status` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Firma digital | `/api/firma/ejecutar` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Firma digital | `/api/firma/status` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Firma digital | `/api/signature/certificates` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Firma digital | `/api/signature/sign` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | IA general/Chat | `/api/agent/feedback` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | IA general/Chat | `/api/ai/providers` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | IA general/Chat | `/api/ai/status` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | IA general/Chat | `/api/chat` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | IA general/Chat | `/api/ia/agent-task` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | IA general/Chat | `/api/ia/consultar` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Usuarios | `/api/usuarios/equipo` | `GET` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
| P2 | Usuarios | `/api/usuarios/registrar` | `POST` | OK | QA+Frontend | `templates/index.html` | Mantener cobertura visual activa y añadir test funcional. |
