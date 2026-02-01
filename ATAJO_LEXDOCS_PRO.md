# 📱 ATAJO: Procesar Documento Legal PRO

## Configuración Manual (Atajos de macOS/iOS)

### PASO 1: Configuración Inicial
1. Abrir app **Atajos**
2. Click **"+"** (Nuevo atajo)
3. Nombre: **"Procesar Documento Legal PRO"**

### PASO 2: Agregar Acciones (en orden)

---

#### 🔹 BLOQUE 1: Selección de Archivos

**Acción 1:** `Seleccionar Archivos`
- Permitir múltiple: ✅ SÍ
- Tipos: Documentos, PDFs, Imágenes

---

#### 🔹 BLOQUE 2: Entrada de Datos

**Acción 2:** `Obtener nombre de` [Archivos]
- Variable: **NombreOriginal**

**Acción 3:** `Pedir Texto`
- Pregunta: "Número de expediente (3 dígitos)"
- Texto por defecto: "015"
- Variable: **NumExpediente**

**Acción 4:** `Pedir Número`
- Pregunta: "¿Año? (ej: 2026)"
- Número por defecto: 2026
- Variable: **Año**

**Acción 5:** `Obtener URL de` 
- URL: `http://localhost:5001/api/icloud/clients`
- Método: GET
- Headers: `Content-Type: application/json`

**Acción 6:** `Obtener contenido de` [URL]
- Variable: **ClientesDisponibles**

**Acción 7:** `Pedir Texto con sugerencias`
- Pregunta: "Nombre del Cliente"
- Sugerencias: [ClientesDisponibles]
- Variable: **Cliente**

**Acción 8:** `Seleccionar del menú`
- Pregunta: "Jurisdicción"
- Opciones:
  - 📋 Civil
  - ⚖️ Penal
  - 💼 Laboral
  - 🏛️ Administrativo
- Variable: **Jurisdiccion**

---

#### 🔹 BLOQUE 3: Procesamiento OCR

**Acción 9:** `Obtener URL de`
- URL: `http://localhost:5001/api/ocr/upload`
- Método: POST
- Headers: `Content-Type: multipart/form-data`
- Body: 
  - Campo: `file`
  - Valor: [Archivos]

**Acción 10:** `Obtener contenido de` [URL]
- Variable: **ResultadoOCR**

**Acción 11:** `Obtener valor de` ResultadoOCR
- Clave: `text`
- Variable: **TextoExtraido**

---

#### 🔹 BLOQUE 4: Detección y Análisis LexNET

**Acción 12:** `Si` [TextoExtraido] **contiene** "LEXNET" o "notificación"

  **Dentro del SI:**
  
  **Acción 13:** `Obtener URL de`
  - URL: `http://localhost:5001/api/lexnet/analyze`
  - Método: POST
  - Headers: `Content-Type: application/json`
  - Body (JSON):
    ```json
    {
      "files": [Archivos],
      "provider": "ollama"
    }
    ```
  
  **Acción 14:** `Obtener contenido de` [URL]
  - Variable: **AnalisisLexNET**
  
  **Acción 15:** `Obtener URL de`
  - URL: `http://localhost:5001/api/icloud/export-analysis`
  - Método: POST
  - Headers: `Content-Type: application/json`
  - Body (JSON):
    ```json
    {
      "content": [AnalisisLexNET],
      "client_name": [Cliente],
      "year": [Año],
      "filename": "ANALISIS_LEXNET_[NumExpediente].txt"
    }
    ```
  
  **Acción 16:** `Mostrar notificación`
  - Título: "✅ Análisis LexNET Completado"
  - Cuerpo: "Exportado a iCloud/EXPEDIENTES/[Año]/[Cliente]/LEXNET/"

**Fin del SI**

---

#### 🔹 BLOQUE 5: Exportación General

**Acción 17:** `Obtener URL de`
- URL: `http://localhost:5001/api/icloud/export`
- Método: POST
- Headers: `Content-Type: application/json`
- Body (JSON):
  ```json
  {
    "content": [TextoExtraido],
    "client_name": [Cliente],
    "year": [Año],
    "category": [Jurisdiccion],
    "filename": "[NumExpediente]_[NombreOriginal]"
  }

Acción 18: Obtener contenido de [URL]


Variable: ResultadoExport
🔹 BLOQUE 6: Notificación Final
Acción 19: Obtener valor de ResultadoExport

Clave: filepath

Variable: RutaFinal
Acción 20: Mostrar notificación

Título: "🎉 Documento Procesado"

Cuerpo:
📁 Expediente: [NumExpediente]
👤 Cliente: [Cliente]
📂 Jurisdicción: [Jurisdiccion]
☁️ Ruta: [RutaFinal]

Acción 21: Mostrar alerta

Título: "✅ Procesamiento Completado"

Mensaje: "Archivo guardado en iCloud Drive"

Botón: "OK"


🚀 USO DEL ATAJO
Desde Mac:
Compartir archivo → Atajos → "Procesar Documento Legal PRO"

Rellenar datos

Esperar procesamiento

✅ Archivo en iCloud automáticamente

Desde iPhone/iPad:
Descargar documento

Abrir Atajos → "Procesar Documento Legal PRO"

Seleccionar archivo

Completar formulario

✅ Sincronizado en iCloud
🔧 CONFIGURACIÓN PARA iPhone/iPad
Para que funcione desde dispositivos móviles, necesitas:
Opción A: Usar ngrok (exponer localhost)
brew install ngrok
ngrok http 5001
# Copia la URL HTTPS y reemplaza localhost:5001 en el atajo

Opción B: IP local de tu Mac
# En Mac, obtén tu IP local:
ifconfig | grep "inet " | grep -v 127.0.0.1

# En el atajo, reemplaza localhost por: http://192.168.X.X:5001

📊 FUNCIONALIDADES INCLUIDAS
✅ OCR automático de documentos
✅ Detección inteligente de notificaciones LexNET
✅ Análisis automático con IA
✅ Exportación organizada a iCloud
✅ Estructura: Año/Cliente/Jurisdicción
✅ Sugerencias de clientes existentes
✅ Nomenclatura automática de archivos
✅ Notificaciones de progreso


🎯 PRÓXIMAS MEJORAS
 OCR multiidioma

 Extracción automática de fechas/plazos

 Recordatorios automáticos

 Integración con Calendario

 Envío automático por email
