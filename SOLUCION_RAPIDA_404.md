# ✅ Solución Rápida - Tests Fallando

## 🔍 Problema Confirmado

**El servidor Flask NO ha cargado los nuevos endpoints** porque fue iniciado ANTES de que añadiéramos el código.

### Evidencia:
- ✅ Usuario admin existe en BD
- ❌ `/api/auth/login` → 404
- ❌ `/api/health` → 404  
- ❌ `/api/dashboard/stats` → 404
- ❌ `/api/lexnet/*` → 404

**Todos los endpoints devuelven 404 = servidor desactualizado**

---

## ⚡ SOLUCIÓN EN 3 PASOS (30 segundos)

### Paso 1: Detener Servidor

```bash
# En la terminal donde corre el servidor, presionar:
Ctrl + C

# O si está en background:
killall python
```

### Paso 2: Reiniciar Servidor

```bash
cd ~/Desktop/PROYECTOS/LexDocsPro-LITE
python run.py
```

**Deberías ver:**
```
 * Running on http://127.0.0.1:5001
 * Debug mode: on
```

### Paso 3: Verificar que Funciona

En **otra terminal**:

```bash
# Test rápido de autenticación
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@lexdocs.com", "password": "admin123"}'
```

**Respuesta esperada (éxito):**
```json
{
  "success": true,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": 1,
    "email": "admin@lexdocs.com",
    "rol": "ADMIN"
  }
}
```

**Respuesta actual (ERROR):**
```html
<!doctype html>
<html lang=en>
<title>404 Not Found</title>
```

---

## 🧪 Ejecutar Tests Una Vez Reiniciado

```bash
cd ~/Desktop/PROYECTOS/LexDocsPro-LITE
./tests/test_master_suite.sh
```

**Ahora deberías ver:**
```
✅ PASS: Login
✅ PASS: Upload notificación
✅ PASS: Listar notificaciones
✅ Suite PASSED: LexNET Notifications

🎉 TODAS LAS SUITES PASARON
Tasa de éxito: 100%
```

---

## 📋 Checklist de Verificación

Antes de ejecutar tests:

- [ ] Servidor Flask detenido completamente
- [ ] Servidor reiniciado con `python run.py`
- [ ] Login manual funciona (curl test arriba)
- [ ] No hay errores en consola del servidor

---

## 🚨 Si Persiste el Problema

### Verificar Proceso del Servidor

```bash
# Ver procesos Python corriendo
ps aux | grep python

# Debería mostrar algo como:
# victor    12345  ... python run.py
```

### Matar TODOS los procesos Python

```bash
killall -9 python
```

### Verificar Puerto 5001

```bash
# Ver qué está usando el puerto 5001
lsof -i :5001

# Si hay algo, matarlo:
lsof -ti:5001 | xargs kill -9
```

### Iniciar con Logging Verbose

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py
```

---

## 💡 Explicación Técnica

Flask **NO recarga automáticamente** los cambios en el código a menos que:

1. **`debug=True`** en `app.run()`
2. **`FLASK_ENV=development`** en entorno
3. **Watchdog activo** (auto-reload)

Como añadimos cientos de líneas de código NUEVO mientras el servidor estaba corriendo, Flask **no vio esos cambios**. Los endpoints existen en el archivo pero no están registrados en la instancia de Flask activa.

**Solución:** Reiniciar el servidor para que Flask lea `run.py` completo.

---

## ✅ Resumen

**Problema:** Servidor desactualizado  
**Causa:** Código añadido después de iniciar servidor  
**Solución:** Reiniciar servidor con `python run.py`  
**Tiempo:** 30 segundos

Una vez reiniciado, **todos los tests deberían pasar** ✅

---

**Última verificación:** 2026-02-04T03:18:32Z
