# 🚀 LexDocsPro LITE v2.0 - CONTEXTO PARA NUEVO HILO

**Fecha:** 1 de febrero de 2026, 17:50 WET  
**Estado:** ✅ PROYECTO BASE COMPLETADO  
**GitHub:** https://github.com/upap1980-tech/lexdocspro-lite  
**Autor:** Víctor M. Francisco

---

## 📊 ESTADO ACTUAL DEL PROYECTO

### ✅ Completado (Hilo 1)

```
✅ PESTAÑA 1: Consultas
   - Explorador de expedientes
   - Chat IA Multi-Proveedor (Ollama + Groq + Perplexity)
   - Consultas rápidas predefinidas
   - Sistema de notificaciones

✅ PESTAÑA 2: Generador de Documentos
   - 12 tipos de documentos legales (Burofax, Demanda Civil, etc.)
   - IA generación sin errores
   - Descargar/Copiar funcionando
   - Validación de campos

✅ PESTAÑA 3: LexNET Analyzer
   - Análisis de notificaciones judiciales
   - OCR integrado (PyMuPDF + Tesseract)
   - Extracción de metadata
   - Exportación TXT

✅ REPOSITORIO GITHUB
   - Código publicado
   - README profesional
   - .gitignore configurado
   - 5 commits históricos
   - Tag v2.0.0 creado
```

---

## 🎯 PLAN DE DESARROLLO - PRÓXIMAS 4 SEMANAS

### **SEMANA 1 (30 min + 10 min) - PUESTA EN PRODUCCIÓN**

#### **1.1 Deploy en Railway (30 minutos)**

**Objetivo:** Publicar app en internet para acceso remoto

**Pasos:**
```bash
# 1. Crear cuenta https://railway.app (gratis, $5/mes crédito)
# 2. Conectar GitHub (login con GitHub, autorizar)
# 3. Crear nuevo proyecto → Import from GitHub
# 4. Seleccionar rama: main
# 5. Railway detecta Flask automáticamente
# 6. Deploy automático
# 7. URL pública: https://lexdocspro-[random].railway.app
```

**Archivos necesarios (ya existen):**
- ✅ `requirements.txt` - Dependencias Python
- ✅ `run.py` - Servidor Flask
- ⏳ `Procfile` - **CREAR**: Instrucciones para Railway
- ⏳ `runtime.txt` - **CREAR**: Versión Python

**Procfile (crear):**
```
web: gunicorn run:app
```

**runtime.txt (crear):**
```
python-3.11.7
```

**Variables de entorno en Railway:**
```
GROQ_API_KEY=tu_groq_key
PERPLEXITY_API_KEY=tu_perplexity_key
FLASK_ENV=production
```

**Resultado esperado:**
```
✅ App accesible en: https://lexdocspro-lite-prod.railway.app
✅ 24/7 sin apagar tu Mac
✅ Dominio personalizado opcional (+$2/mes)
```

---

#### **1.2 Google Analytics (10 minutos)**

**Objetivo:** Medir uso de la app

**Pasos:**
```bash
# 1. Ir a https://analytics.google.com
# 2. Crear nueva propiedad
# 3. Nombre: "LexDocsPro LITE"
# 4. URL: https://lexdocspro-lite-prod.railway.app
# 5. Obtener Tracking ID: G-XXXXXXXX
```

**Integración en HTML (3 líneas):**

Agregar a `templates/base.html` antes de `</head>`:
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXX');
</script>
```

**Eventos personalizados (en JavaScript):**
```javascript
// Cuando se genera un documento
gtag('event', 'documento_generado', {
  'tipo': 'burofax',
  'proveedor': 'ollama',
  'duracion': 5.2
});

// Cuando se consulta IA
gtag('event', 'consulta_ia', {
  'proveedor': 'groq',
  'tipo_consulta': 'analisis'
});
```

**Dashboard Analytics:**
```
✅ Ver usuarios en tiempo real
✅ Documentos más usados
✅ Horas pico
✅ Dispositivos
✅ Geolocalización
```

---

### **SEMANA 2 (2 horas) - AUTOMATIZACIÓN DE DESPACHO**

#### **2.1 auto_procesar.py Mejorado**

**Objetivo:** Monitorear carpeta PENDIENTES y organizar documentos automáticamente

**Archivo existe:** ✅ `auto_procesar.py` (base)

**Mejoras a implementar:**

1. **Base de datos de eventos**
```python
# SQLite para historial
- Documento recibido
- IA análisis realizado
- Cliente detectado
- Archivo guardado
- Timestamp/Usuario
```

2. **API mejorada**
```python
# Integración con LexDocsPro
- Endpoint: /api/auto/process/history
- Endpoint: /api/auto/stats
- Endpoint: /api/auto/rules (reglas personalizadas)
```

3. **Reglas personalizadas**
```python
# Usuario puede crear reglas
Si cliente == "2026_0000068" → Carpeta "Casos Importantes"
Si tipo_doc == "Sentencia" → Notificación urgente
Si palabra_clave == "embargo" → Alerta roja
```

4. **Exportación automática**
```python
# Guardar en:
- Local (carpetas organizadas)
- Google Drive (sync automático)
- OneDrive (sync automático)
- iCloud Drive
```

5. **Integración de emails**
```python
# Detectar PDFs en Gmail y descargarlos automáticamente
- IMAP de Gmail
- Descargar adjuntos
- Guardar en PENDIENTES
- Procesar con auto_procesar.py
```

**Timeline Semana 2:**
```
Lunes: Mejorar base de datos (1 hora)
Martes: Agregar reglas personalizadas (30 min)
Miércoles: Integración Google Drive (30 min)
Jueves: Testing y refinamiento (1 hora)
```

---

### **MES 1 (4 horas) - DASHBOARD PERSONALIZADO**

#### **3.1 Dashboard de Control**

**Objetivo:** Panel administrativo con métricas, estadísticas y controles

**Estructura:**

```
╔════════════════════════════════════════════════════════════╗
║                 📊 DASHBOARD LEXDOCSPRO LITE               ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  🎯 ESTADÍSTICAS PRINCIPALES (KPIs)                       ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ Docs Generados: 124  │ Usuarios: 8  │ Uptime: 99.7% │ ║
║  │ Consultas IA: 456    │ OCRs: 45     │ Storage: 2.1GB │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                            ║
║  📈 GRÁFICOS                                               ║
║  ┌──────────────────────────┬──────────────────────────┐  ║
║  │ Documentos por Tipo      │ Uso por Hora (últimas24) │  ║
║  │ (Pastel: Burofax 40%)    │ (Línea temporal)         │  ║
║  │  Demanda 25%             │ Pico: 14:30 (12 docs)    │  ║
║  │  Recursos 20%            │ Bajo: 03:00 (1 doc)      │  ║
║  │  Otros 15%               │                          │  ║
║  └──────────────────────────┴──────────────────────────┘  ║
║                                                            ║
║  🤖 PROVEEDORES IA                                         ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ Ollama: 180 consultas (45%)                          │ ║
║  │ Groq:   156 consultas (39%)                          │ ║
║  │ Perplexity: 64 consultas (16%)                       │ ║
║  │ Tiempo promedio: 4.2 segundos                        │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                            ║
║  🚨 ALERTAS                                                ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ ⚠️ Storage 85% (limpiar documentos antiguos)         │ ║
║  │ ✅ Ollama conectado y funcionando                    │ ║
║  │ ✅ Groq API respondiendo normalmente                 │ ║
║  │ ❌ 3 errores de OCR (necesita revisión manual)       │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                            ║
║  ⚙️ CONFIGURACIÓN Y CONTROLES                             ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │ [🔘 Modo Automático] [📅 Backup] [🔄 Sincronizar]   │ ║
║  │ [🗑️ Limpiar Cache] [📊 Exportar Datos] [⚙️ Ajustes]  │ ║
║  └──────────────────────────────────────────────────────┘ ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

**Componentes a desarrollar:**

1. **Backend (Flask routes)** - 1 hora
```python
@app.route('/admin/dashboard')
def dashboard():
    """Página principal del dashboard"""
    stats = {
        'docs_generados': count_documents(),
        'usuarios_activos': count_active_users(),
        'uptime': calculate_uptime(),
        'docs_por_tipo': get_docs_by_type(),
        'consultas_ia': get_ia_queries(),
        'errores': get_recent_errors()
    }
    return render_template('dashboard.html', stats=stats)

# Endpoints para datos
@app.route('/api/admin/stats')
@app.route('/api/admin/charts/docs-by-type')
@app.route('/api/admin/charts/hourly-usage')
@app.route('/api/admin/alerts')
@app.route('/api/admin/ia-providers')
```

2. **Frontend (HTML + Charts)** - 1.5 horas
```html
<!-- templates/dashboard.html -->
<!-- Cards KPI -->
<!-- Gráficos (Chart.js) -->
<!-- Tabla de alertas -->
<!-- Controles de configuración -->
```

3. **Gráficos en tiempo real** - 1 hora
```javascript
// Chart.js para visualizaciones
- Documentos por tipo (Pastel)
- Uso por hora (Línea)
- Rendimiento IA (Barras)
- Status de proveedores (Gauge)
```

4. **Sistema de alertas** - 0.5 horas
```python
# Monitorear:
- Storage disponible
- Conexión IA providers
- Errores del sistema
- Usuarios simultáneos
```

---

## 📁 ESTRUCTURA DE ARCHIVOS ACTUAL

```
LexDocsPro-LITE/
├── run.py                          # Servidor Flask
├── requirements.txt                # Dependencias
├── .gitignore                      # Git ignore
├── README.md                       # Documentación
│
├── services/
│   ├── ai_service.py              # IA Multi-proveedor
│   ├── document_generator.py       # Generador de docs
│   ├── ocr_service.py             # OCR
│   └── lexnet_analyzer.py         # Analizador LexNET
│
├── static/
│   ├── css/
│   │   └── style.css              # Estilos
│   └── js/
│       └── app.js                 # JavaScript
│
├── templates/
│   ├── base.html                  # Base HTML
│   ├── index.html                 # Página principal
│   └── dashboard.html             # ⏳ Dashboard (crear)
│
├── data/
│   ├── analytics.jsonl            # Eventos analytics
│   └── documents.db               # SQLite
│
└── auto_procesar.py               # Monitor automático
```

---

## 🔧 CONFIGURACIÓN REQUERIDA PARA PRÓXIMOS HILO

### **Credenciales a tener listos:**
```
GROQ_API_KEY=...          (Ya tienes)
PERPLEXITY_API_KEY=...    (Ya tienes)
OLLAMA_URL=...            (Ya tienes)
```

### **Cuentas a crear (gratuitas):**
```
✅ Railway.app              (Hosting)
✅ Google Analytics         (Analytics)
⏳ GitHub Actions          (CI/CD - opcional)
```

### **Comandos básicos a recordar:**
```bash
# Activar venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor local
python run.py

# Ejecutar monitor automático
python auto_procesar.py

# Push a GitHub
git add .
git commit -m "tu mensaje"
git push origin main
```

---

## 📊 MÉTRICAS ESPERADAS DESPUÉS DE MES 1

```
✅ App en producción 24/7
   └─ URL: https://lexdocspro-lite.railway.app

✅ Datos de uso disponibles en Google Analytics
   └─ Documentos generados/mes
   └─ Usuarios activos
   └─ Documentos más usados

✅ auto_procesar.py automatizando despacho
   └─ Documentos procesados automáticamente
   └─ Historial de eventos

✅ Dashboard profesional
   └─ Métricas en tiempo real
   └─ Gráficos interactivos
   └─ Sistema de alertas
   └─ Controles administrativos

KPIs OBJETIVO:
├─ Uptime: >99.5%
├─ Documentos/mes: 100+
├─ Usuarios activos: 20+
├─ Tiempo respuesta: <2s
└─ Tasa éxito: >95%
```

---

## 🎯 PRIORIDADES PARA NUEVO HILO

### **Orden recomendado:**

1. **INMEDIATO (Hoy/Mañana):**
   - Deploy en Railway (30 min)
   - Google Analytics (10 min)
   - Crear `Procfile` y `runtime.txt`
   - Commit y push a GitHub

2. **SEMANA 1 (próximos 3-4 días):**
   - Verificar app en producción
   - Revisar Google Analytics
   - Crear primeras métricas

3. **SEMANA 2:**
   - Mejorar auto_procesar.py
   - Agregar base de datos
   - Integrar reglas personalizadas

4. **MES 1:**
   - Dashboard completo
   - Gráficos en tiempo real
   - Sistema de alertas

---

## 📞 CONTACTO E INFORMACIÓN

**Proyecto:** LexDocsPro LITE v2.0  
**Autor:** Víctor M. Francisco  
**GitHub:** https://github.com/upap1980-tech/lexdocspro-lite  
**Email:** upap1980@gmail.com  
**Versión:** v2.0.0 (Tag: v2.0.0)  

**Ubicación local:**
```
/Users/victormfrancisco/Desktop/PROYECTOS/LexDocsPro-LITE
```

**Directorios importantes:**
```
EXPEDIENTES: /Users/victormfrancisco/Desktop/EXPEDIENTES
PENDIENTES: /Users/victormfrancisco/Desktop/PENDIENTES_LEXDOCS
GENERADOS: /Users/victormfrancisco/Desktop/EXPEDIENTES/_GENERADOS
```

---

## ✅ CHECKLIST PARA NUEVO HILO

- [ ] Revisar este contexto
- [ ] Tener credenciales IA listos
- [ ] Tener cuenta Railway creada
- [ ] Tener cuenta Google Analytics creada
- [ ] Terminal abierta en carpeta proyecto
- [ ] GitHub branch main actualizado
- [ ] Python venv activado

---

**Documento creado:** 1 de febrero de 2026  
**Próximo paso:** Continuar en nuevo hilo con Deploy en Railway
