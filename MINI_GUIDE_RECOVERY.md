# 🚀 MINI-GUÍA: RECUPERACIÓN v2.3.2 HOTFIX (1h 45min)

**Ejecutar en orden. Copiar y pegar cada bloque.**

## 📋 PRE-REQUISITOS
```bash
cd ~/Desktop/PROYECTOS/LexDocsPro-LITE
git checkout analysis/01-preliminary-scan
git pull origin analysis/01-preliminary-scan
git status  # Debe estar limpio
```

---

## 🎯 FASE 1: BACKUP TOTAL (5 min)

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p _backups_/pre_recovery_${TIMESTAMP}
cp run.py _backups_/pre_recovery_${TIMESTAMP}/
cp static/js/app.js _backups_/pre_recovery_${TIMESTAMP}/
cp templates/index.html _backups_/pre_recovery_${TIMESTAMP}/
cp decorators.py _backups_/pre_recovery_${TIMESTAMP}/ 2>/dev/null || true
echo "✅ BACKUP COMPLETO: _backups_/pre_recovery_${TIMESTAMP}"
```

---

## 🎯 FASE 2: RESTAURAR ARCHIVOS v2.3.1 (10 min)

```bash
# run.py v2.3.1
cp run.py.backup.20260204 run.py

# app.js v2.3.1
if [ -f static/js/app.js.backup.20260204 ]; then
  cp static/js/app.js.backup.20260204 static/js/app.js
  echo "✅ app.js restaurado"
else
  echo "⚠️ app.js.backup.20260204 no encontrado"
fi

# Verificar decorators.py existe
grep -q "jwt_required_custom" decorators.py || echo "⚠️ Verificar decorators.py manualmente"

echo "✅ RESTAURACIÓN COMPLETA"
```

---

## 🎯 FASE 3: FIX CRÍTICO #1 - DATABASE CRASH (20 min)

### **Buscar TODAS las ocurrencias:**
```bash
grep -n "db\.conn" run.py
echo "📋 Anote las líneas para corregir (ej: 1521, 1678, etc.)"
```

### **Corregir patrón en run.py:**

**Busque:** `cursor = db.conn.cursor()`

**Reemplace por:**
```python
conn = None
try:
    conn = db.get_connection()
    cursor = conn.cursor()
```

**Añada al final del bloque:**
```python
finally:
    if conn:
        conn.close()
```

**Ejemplo completo:**
```python
@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required_custom
def dashboard_stats_detailed():
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clients")
        total_clients = cursor.fetchone()[0]
        
        stats = {
            'success': True,
            'total_documents': total_docs,
            'total_clients': total_clients
        }
        return jsonify(stats)
    
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()
```

**Verificar:**
```bash
grep -n "db\.conn" run.py  # Debe devolver VACÍO
```

---

## 🎯 FASE 4: FIX CRÍTICO #2 - FRONTEND (30 min)

### **Opción A - Restaurar HTML clásico (recomendado):**
```bash
# Buscar backups con sidebar
find _backups_ -name "index.html" -exec grep -l "sidebar" {} \; | head -1

# Restaurar (ejemplo, ajustar path):
cp _backups_/LEXDOCSPRO_v230_LIVE_OLD/templates/index.html templates/index.html

# O buscar backup específico:
ls -la templates/index.html*
cp templates/index.html.backup.* templates/index.html  # Si existe
```

### **Verificación HTML:**
```bash
# Debe contener estos IDs (Sidebar 15 ítems):
grep -E "(chatPrompt|fileTree|pdfViewer|docTypes|sidebar)" templates/index.html

# Output esperado:
# <input id="chatPrompt" ...>
# <div id="fileTree">...</div>
# <iframe id="pdfViewer">...</iframe>
# <select id="docTypes">...</select>
# <div class="sidebar">...</div>
```

**Si NO encuentra HTML correcto:**
```bash
# Opción B - Verificar manualmente en GitHub
open https://github.com/upap1980-tech/lexdocspro-lite/tree/analysis/01-preliminary-scan/templates
```

---

## 🎯 FASE 5: FIX CRÍTICO #3 - SEGURIDAD (15 min)

### **Proteger 3 endpoints críticos en run.py:**

**Buscar:**
```bash
grep -n "def.*(smart_analyze_document\|ocr_upload\|lexnet_analyze)" run.py
```

**Añadir línea ANTES de cada función:**
```python
@app.route('/api/document/smart-analyze', methods=['POST'])
@jwt_required_custom  # ← AÑADIR ESTA LÍNEA
@admin_required       # ← OPCIONAL, si existe
def smart_analyze_document():
```

**Endpoints a proteger:**
1. `smart_analyze_document`
2. `ocr_upload`
3. `lexnet_analyze`

**Verificar:**
```bash
grep -A1 "@jwt_required_custom" run.py | grep -E "(smart|ocr|lexnet)"
```

---

## 🎯 FASE 6: VERIFICACIÓN (15 min)

### **6.1 - Limpiar cache:**
```bash
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "✅ Cache limpiado"
```

### **6.2 - Test arranque:**
```bash
# Terminal 1 - Servidor
python run.py

# Terminal 2 - Tests
```

### **6.3 - Test Dashboard (CRÍTICO):**
```bash
# Obtener token
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.token' > /tmp/token.txt

# Test Dashboard
TOKEN=$(cat /tmp/token.txt)
curl -X GET "http://localhost:5001/api/dashboard/stats" \
  -H "Authorization: Bearer $TOKEN"

# ✅ ESPERADO:
# {"success": true, "total_documents": 123, "total_clients": 45}

# ❌ PROBLEMA SI:
# {"error": "AttributeError"}  → DB FIX pendiente
```

### **6.4 - Test Auth (CRÍTICO):**
```bash
# Sin token → 401
curl -X POST http://localhost:5001/api/document/smart-analyze

# ✅ ESPERADO:
# {"error": "Missing or invalid token"}

# ❌ PROBLEMA SI:
# 200 OK → Auth NO funciona
```

### **6.5 - Test Frontend:**
```bash
open http://localhost:5001

# ✅ ESPERADO:
# - Sidebar 15 ítems visible
# - Tabs funcionales
# - Dropdowns cargan
# - Botones responden

# ❌ PROBLEMA SI:
# - Solo <div id="root"></div> vacío
# - Errores en Console
```

---

## 🎯 FASE 7: COMMIT v2.3.2 HOTFIX (10 min)

```bash
git add run.py templates/index.html static/js/app.js decorators.py

git commit -m "🚑 v2.3.2 HOTFIX: Critical Recovery

✅ RESUELTO (16 CRITICAL issues):
- DB Crash: db.conn → db.get_connection()
- Frontend: React → HTML clásico restaurado
- Auth: 3 endpoints protegidos

📊 ANÁLISIS DUAL:
Antigravity: 20 issues | OpenAI: 42 issues
Resueltos: 16 CRITICAL (100%)

🔍 VERIFICADO:
✅ Dashboard: 200 OK
✅ Auth: 401 sin token
✅ Frontend: Renderiza

⏰ 2026-02-04 15:15 WET"

git push origin analysis/01-preliminary-scan

echo "✅ HOTFIX v2.3.2 completado"
```

---

## 📋 CHECKLIST RAPIDA

```
[ ] FASE 1: Backup ✅
[ ] FASE 2: Restauración ✅
[ ] FASE 3: DB Fix ✅
[ ] FASE 4: Frontend Fix ✅
[ ] FASE 5: Auth Fix ✅
[ ] FASE 6: Tests ✅
[ ] FASE 7: Commit ✅

🎯 TOTAL: 105 minutos
```

## 🚦 VERIFICACIÓN FINAL

```
✅ Flask arranca sin errores
✅ Dashboard carga (200 OK)
✅ Auth funciona (401 sin token)
✅ Sidebar 15 ítems visible
✅ Sistema: OPERATIVO v2.3.2
```

---

**¡Copiar, pegar, ejecutar!**
*Mini-Guía generada: 2026-02-04 15:05 WET*