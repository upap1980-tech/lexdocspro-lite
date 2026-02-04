# 🎓 **TUTORIAL COMPLETO - LexDocsPro v3.0 PRO**

## 📚 **MANUAL DE USO POR SECCIÓN**

---

## **1️⃣ DASHBOARD - Panel de Control**

### **Qué es:**
Pantalla principal que muestra estadísticas en tiempo real de tu sistema legal.

### **Cómo usar:**
1. **Al abrir** `http://localhost:5001` → Estás aquí automáticamente
2. Ver **4 tarjetas de estadísticas**:
   - 📄 Total Documentos generados
   - 📁 Total Expedientes creados
   - 🔔 Documentos generados HOY
   - 🤖 Modelos IA disponibles

### **Ejemplo de uso:**
```
Mañana amaneces, abres LexDocsPro
↓
Ves que generaste 12 documentos
↓
3 expedientes abiertos
↓
Sabes exactamente el estado de tu sistema
```

### **Tips:**
- Dashboard se **auto-actualiza** cada 30s
- Si muestra "0 documentos" = servidor sin datos (normal en primera vez)
- Los números crecen conforme usas el sistema

---

## **2️⃣ CHAT LEGAL - Asesor Virtual**

### **Qué es:**
IA que responde preguntas legales contextualizadas a derecho español.

### **Cómo usar:**

#### **Opción A - Escribir pregunta libre:**
```
1. Click en "💬 Chat Legal"
2. En el cuadro inferior, escribe:
   "¿Cuáles son los requisitos de una demanda civil?"
3. Click en "📤 Enviar Consulta"
4. Espera 2-5 segundos (Ollama local)
5. Recibe respuesta formateada
```

#### **Opción B - Usar ejemplos pre-hechos:**
```
Click en uno de estos botones:
→ "Plazo apelación"
→ "Delito estafa"
→ "Demanda civil"

Automáticamente envía la pregunta
```

### **Ejemplos de preguntas:**
```
✅ "¿Cuál es el plazo para recurrir una sentencia?"
✅ "Explica los elementos del delito de estafa"
✅ "¿Qué requisitos tiene una demanda laboral?"
✅ "¿Cuál es la jurisdicción para un caso civil?"
✅ "¿Qué es una medida cautelar?"
```

### **Cómo cambiar modelo:**
```
1. En el header superior, hay selector:
   - Ollama (Local) ← Gratis, rápido en tu Mac
   - Groq (Rápido) ← Necesita API KEY (gratis)
   - OpenAI (GPT) ← De pago, mejor calidad
   
2. Selecciona uno
3. El siguiente mensaje usa ese modelo
```

### **Tips:**
- **Ollama**: 2-5 segundos, corre en tu Mac, sin latencia internet
- **Groq**: 50ms, super rápido, gratis con cuenta
- **OpenAI**: 100ms, mejor comprensión legal, de pago

---

## **3️⃣ GENERADOR - Redacción Automática**

### **Qué es:**
IA que redacta 12 tipos de documentos legales profesionales.

### **Cómo usar:**

```
PASO 1: Click en "📄 Generador"

PASO 2: Selecciona tipo de documento
        Verás 12 botones:
        ✓ Demanda Civil
        ✓ Contestación
        ✓ Recurso Apelación
        ... etc

PASO 3: Escribe descripción del caso
        Ejemplo:
        "Cliente demanda a empresa constructora 
         por incumplimiento de contrato de obra.
         Daños por retrasos: 50.000€.
         Obra sin terminar hace 6 meses."

PASO 4: Click "⚡ Generar Documento"

PASO 5: Espera 5-10 segundos

PASO 6: Documento generado aparece
        Click "📋 Copiar" o "💾 Descargar"
```

### **Ejemplo COMPLETO:**

**Entrada:**
```
Tipo: Demanda Civil
Descripción: 
"Mi cliente vendió inmueble por 200.000€.
El comprador no pagó.
Necesito demanda por incumplimiento."
```

**Salida (IA genera automáticamente):**
```
DEMANDA ORDINARIA CIVIL
Juzgado de Primera Instancia Nº... [COMPLETO]

PARTE DEMANDANTE:
[Datos generados]

PARTE DEMANDADA:
[Datos generados]

HECHOS:
1. [Contexto de la venta]
2. [Incumplimiento de pago]
3. [Pretensiones]

FUNDAMENTOS JURÍDICOS:
[Artículos aplicables]

PARTE DISPOSITIVA:
[Lo que pide]
```

### **Los 12 documentos:**

1. **Demanda Civil** → Litigios civiles ordinarios
2. **Contestación** → Responder a una demanda
3. **Recurso Apelación** → Recurrir sentencia
4. **Demanda Penal** → Acusación penal
5. **Medida Cautelar** → Asegurar resultado
6. **Recurso Amparo** → Ante Tribunal Const.
7. **Demanda Laboral** → Litigios laborales
8. **Demanda Admin** → Contencioso-administrativo
9. **Contrato Servicios** → Acuerdos comerciales
10. **Poder Notarial** → Poderes y apoderamiento
11. **Acta Junta** → Actas de reuniones
12. **Cláusulas** → Redacción libre

### **Tips:**
- **Ser específico** → Mejor documento
- **Detallar hechos** → Más contextualizado
- **Fechas importantes** → Se incluyen automáticamente
- **Cambiar modelo** → Usa selector superior

---

## **4️⃣ ANALIZADOR LEXNET - OCR + Extracción**

### **Qué es:**
Analiza automáticamente documentos judiciales españoles (PDFs/TXT) y extrae:
- Partes (demandante, demandado)
- Tipo de procedimiento
- Tribunal/Juzgado
- Número de procedimiento
- **Plazos legales** (con alertas)
- Medidas cautelares
- Próximos pasos

### **Cómo usar:**

```
PASO 1: Click en "🔍 Analizador LexNET"

PASO 2: Arrastra o selecciona archivos
        Soporta:
        ✓ PDF (se lee con OCR)
        ✓ TXT (texto plano)
        ✓ Múltiples archivos

PASO 3: Click "🔍 Analizar"

PASO 4: Espera 3-8 segundos

PASO 5: Recibe análisis completo:
        ✓ Datos extraídos (JSON)
        ✓ Plazos identificados
        ✓ Urgencias (CRÍTICO/NORMAL)
```

### **Ejemplo de ANÁLISIS:**

**Input**: PDF del Juzgado Provincial de Barcelona

**Output**:
```
✅ ANÁLISIS COMPLETADO

⏰ PLAZOS:
├─ Recurso Apelación
│  ├─ Plazo: 20 días
│  ├─ Fecha límite: 2026-02-21
│  ├─ Art. 131 LEC
│  └─ Urgencia: 🔴 CRÍTICO (2 días restantes)
│
└─ Medida Cautelar
   ├─ Plazo: 5 días
   ├─ Fecha límite: 2026-02-06
   ├─ Art. 727 LEC
   └─ Urgencia: 🟢 NORMAL

📋 DATOS EXTRAÍDOS:
├─ Demandante: Juan García López
├─ Demandado: Empresa ABC SL
├─ Tribunal: Audiencia Provincial de Barcelona
├─ Procedimiento: Apelación Civil
└─ Número: 2026/00123/CA
```

### **Detección automática:**

La IA identifica automáticamente:
- ✅ Recurso Apelación → 20 días (Art. 131 LEC)
- ✅ Recurso Amparo → 30 días (Art. 44 LOTC)
- ✅ Medida Cautelar → 5 días (Art. 727 LEC)
- ✅ Demanda Civil → 5 días (Art. 405 LEC)
- ✅ Recurso Administrativo → 2 meses

### **Colores de urgencia:**
- 🔴 **CRÍTICO** → Menos de 2 días (¡ACTÚA YA!)
- 🟡 **URGENTE** → 2-7 días (prioridad)
- 🟢 **NORMAL** → Más de 7 días (tranquilo)

### **Tips:**
- Funciona con **PDFs escaneados** (OCR)
- Múltiples documentos → Análisis combinado
- Extrae automáticamente **números de procedimiento**
- Calcula plazos **desde hoy**

---

## **5️⃣ EXPEDIENTES - Gestor de Casos**

### **Qué es:**
CRUD completo para gestionar tus expedientes/casos legales.

### **Cómo usar:**

#### **Crear expediente:**
```
1. Click "📁 Expedientes"
2. Click "➕ Nuevo Expediente"
3. Completa:
   - Título: "Caso García vs ABC SL"
   - Tipo: "civil"
4. Click crear
5. Aparece en lista
```

#### **Ver expedientes:**
```
Aparecen como tarjetas con:
✓ Título del caso
✓ Tipo (civil/penal/admin)
✓ Número de documentos
✓ Fecha de creación
```

#### **Gestionar documentos:**
```
Cada expediente puede contener:
- Demandas
- Sentencias
- Recursos
- Pruebas
- Informes periciales
```

### **Ejemplo:**
```
EXPEDIENTE: "García vs Constructora ABC"
├─ Demanda Civil (01-Feb-2026)
├─ Contestación (10-Feb-2026)
├─ Prueba Pericial (15-Feb-2026)
└─ Sentencia (Pendiente)
```

### **Tips:**
- Organiza por **año y tipo**
- Vincula **documentos generados**
- Exporta a **iCloud** (en desarrollo)

---

## **6️⃣ CONFIGURACIÓN - Panel Admin**

### **Qué es:**
Configura modelos IA y opciones avanzadas.

### **Opciones:**

#### **1. Modelo Ollama (Local)**
```
Opciones:
- lexdocs-legal-pro (recomendado)
- mistral (rápido)
- llama3 (equilibrado)

Acción: Reinicia servidor
```

#### **2. Groq API Key (Gratis)**
```
1. Regístrate: https://console.groq.com
2. Copia tu API KEY (gsk_...)
3. Pega en "Groq API Key"
4. Click "💾 Guardar"
5. Ahora tienes acceso a Groq (50ms respuestas)
```

#### **3. OpenAI API Key (De pago)**
```
1. Regístrate: https://platform.openai.com
2. Copia tu API KEY (sk_...)
3. Pega en "OpenAI API Key"
4. Click "💾 Guardar"
5. Ahora tienes acceso a GPT-4
```

### **Tips:**
- Ollama = **GRATIS**, local, sin límites
- Groq = **GRATIS**, rápido, 15 req/min free
- OpenAI = **De pago**, mejor calidad

---

## **⌨️ ATAJOS DE TECLADO**

```
TAB 1: Personalizado (próximo)
TAB 2: Personalizado (próximo)
ENTER: Enviar mensaje en Chat
CTRL+K: Buscar documento
CTRL+S: Guardar configuración
CMD+L: Focus en chat input
```

---

## **🔧 SOLUCIÓN DE PROBLEMAS**

### **No aparecen documentos:**
```
✓ Verifica que Ollama esté corriendo
✓ Revisa terminal de errores
✓ Reinicia servidor: python run.py
```

### **Chat muy lento:**
```
✓ Cambiar a Groq (más rápido)
✓ Cambiar a OpenAI (más rápido)
✓ Verifica memoria disponible (free -h)
```

### **OCR no funciona:**
```
✓ Instala Tesseract: brew install tesseract
✓ Verifica: tesseract --version
```

### **Puerto 5001 en uso:**
```
✓ Mata el proceso: lsof -i :5001 | grep LISTEN
✓ Kill: kill -9 <PID>
```

---

## 🎓 **RECAPITULACIÓN**

| Sección | Usa para | Entrada | Salida |
|---------|----------|---------|--------|
| Dashboard | Ver estado | - | Estadísticas |
| Chat | Consultas legales | Pregunta | Respuesta IA |
| Generador | Redactar documentos | Descripción | Documento .txt |
| LexNET | Analizar expedientes | PDF/TXT | Datos + Plazos |
| Expedientes | Organizar casos | Datos caso | Carpeta digital |
| Config | Ajustar sistema | API Keys | Sistema activo |

---

**¡Ahora eres experto en LexDocsPro v3.0 PRO!** 🚀
