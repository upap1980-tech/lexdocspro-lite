# 🎯 ATAJO SIMPLIFICADO - Versión 1.0

## Acciones a agregar (búscalas en el panel derecho):

### 1. Seleccionar Archivos
- Busca: "Seleccionar archivos"
- Arrastra al editor
- Configuración:
  ✅ Permitir múltiples archivos
  ✅ Tipos: Todos

### 2. Pedir Expediente
- Busca: "Pedir información"
- Arrastra al editor
- Configuración:
  - Pregunta: "Número de expediente"
  - Tipo: Texto
  - Valor por defecto: "015"

### 3. Pedir Año
- Busca: "Pedir información"
- Arrastra al editor
- Configuración:
  - Pregunta: "Año"
  - Tipo: Número
  - Valor por defecto: 2026

### 4. Pedir Cliente
- Busca: "Pedir información"
- Arrastra al editor
- Configuración:
  - Pregunta: "Nombre del cliente"
  - Tipo: Texto

### 5. Menú de Jurisdicción
- Busca: "Elegir del menú"
- Arrastra al editor
- Configuración:
  - Pregunta: "Jurisdicción"
  - Opciones:
    1. Civil
    2. Penal
    3. Laboral
    4. Administrativo

### 6. Obtener contenido de URL (OCR)
- Busca: "Obtener contenidos de URL"
- Arrastra al editor
- Configuración:
  - URL: http://localhost:5001/api/ocr/upload
  - Método: POST
  - Tipo de solicitud: Formulario
  - Click "Añadir campo de formulario":
    - Nombre: file
    - Valor: [Seleccionar "Archivos" de variables]

### 7. Exportar a iCloud
- Busca: "Obtener contenidos de URL"
- Arrastra al editor
- Configuración:
  - URL: http://localhost:5001/api/icloud/export
  - Método: POST
  - Headers:
    - Content-Type: application/json
  - Cuerpo de solicitud: JSON
  - Click en "{}" para editar JSON:

```json
{
  "content": "Contenidos de URL",
  "client_name": "Texto proporcionado",
  "year": "Número proporcionado",
  "category": "Elemento de menú",
  "filename": "Nombre de archivo"
}

8. Mostrar Notificación
Busca: "Mostrar notificación"

Arrastra al editor

Configuración:

Título: ✅ Documento Procesado

Cuerpo: Guardado en iCloud Drive
🎬 CÓMO CONECTAR LAS VARIABLES
En cada acción que pida datos de pasos anteriores:

Click en el campo

Se abre menú de "Variables"

Selecciona la variable del paso anterior:

"Texto proporcionado" → Cliente

"Número proporcionado" → Año

"Elemento de menú" → Jurisdicción

"Archivos" → Archivo seleccionado

"Contenidos de URL" → Resultado OCR

✅ PROBAR EL ATAJO
Click en ▶️ (Play) arriba a la derecha

Selecciona un PDF de prueba

Rellena los datos

¡Debería procesar y exportar!

