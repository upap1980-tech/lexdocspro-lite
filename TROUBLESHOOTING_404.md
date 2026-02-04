# 🐛 Troubleshooting: Tests Fallando con 404

**Problema:** Todos los endpoints devuelven 404 Not Found

## 🔍 Diagnóstico

El servidor Flask está corriendo pero devuelve 404 para todos los endpoints, incluyendo:
- `/api/auth/login`
- `/api/health`
- `/api/dashboard/stats`
- `/api/document/preview`
- `/api/lexnet/*`

## ✅ Causa Raíz

**El servidor fue iniciado ANTES de que añadiéramos los nuevos endpoints.**

Flask carga todos los endpoints al iniciar. Si el servidor estaba corriendo cuando añadimos el código nuevo, los endpoints NO se registran hasta que reiniciemos el servidor.

## 🔧 Solución (3 pasos)

### 1. Detener el Servidor

**Opción A:** Si el servidor está en una terminal visible:
```bash
# Presionar Ctrl+C en la terminal donde corre el servidor
```

**Opción B:** Si el servidor está en background:
```bash
# Buscar proceso
ps aux | grep "python run.py"

# Matar proceso (reemplazar PID con el número del proceso)
kill <PID>

# O forzar
killall python
```

**Opción C:** Si está en tmux/screen:
```bash
# Listar sesiones tmux
tmux ls

# Adjuntar a sesión
tmux attach -t <nombre-sesion>

# Presionar Ctrl+C
```

### 2. Reiniciar el Servidor

```bash
cd ~/Desktop/PROYECTOS/LexDocsPro-LITE

# Iniciar servidor
python run.py
```

**Deberías ver output similar a:**
```
 * Running on http://127.0.0.1:5001
 * Debug mode: on
WARNING: This is a development server.
```

### 3. Verificar que Carga Correctamente

**Test rápido:**
```bash
# En otra terminal
curl http://localhost:5001/api/health
```

**Respuesta esperada:**
```json
{"status":"ok"}
```

Si ves esto, los endpoints están cargados ✅

## 🧪 Re-ejecutar Tests

Una vez reiniciado el servidor:

```bash
cd ~/Desktop/PROYECTOS/LexDocsPro-LITE

# Ejecutar suite maestra
./tests/test_master_suite.sh
```

**Ahora deberías ver:**
```
✅ Suite PASSED: Document Confirmation
✅ Suite PASSED: LexNET Notifications
🎉 TODAS LAS SUITES PASARON
```

---

## 📋 Checklist de Verificación

Antes de ejecutar tests:

- [ ] Servidor detenido completamente
- [ ] Servidor reiniciado con `python run.py`
- [ ] Health check responde OK
- [ ] Puerto 5001 activo (`lsof -i :5001`)
- [ ] No hay errores en consola del servidor

---

## 🔍 Verificación Adicional

Si después de reiniciar siguen los 404:

### Verificar que run.py carga correctamente

```bash
python -c "
import run
print('✅ run.py carga sin errores')
print(f'Rutas registradas: {len(run.app.url_map._rules)}')
"
```

### Listar todos los endpoints

```bash
# En Python shell
python
>>> import run
>>> for rule in run.app.url_map.iter_rules():
...     print(f"{rule.rule} -> {rule.endpoint}")
>>> exit()
```

Deberías ver:
```
/api/auth/login -> auth.login
/api/lexnet/upload-notification -> lexnet_upload_notification
/api/document/preview -> document_preview
/api/dashboard/stats-detailed -> dashboard_stats_detailed
...
```

### Verificar blueprint de auth

```bash
python
>>> from auth_blueprint import auth_bp
>>> print(auth_bp.url_prefix)  # Debe ser: /api/auth
>>> exit()
```

---

## 💡 Consejos para Desarrollo

### Modo Hot-Reload (Recomendado)

Para auto-reload cuando cambias código:

```bash
export FLASK_ENV=development
python run.py
```

O modificar `run.py` al final:

```python
if __name__ == '__main__':
    app.run(
        debug=True,      # ✅ Activa hot-reload
        host='0.0.0.0',
        port=5001
    )
```

**Con debug=True:**
- Servidor se reinicia automáticamente al cambiar código
- Tracebacks detallados en errores
- NO usar en producción

---

## 🚨 Problemas Comunes

### ERROR: "Address already in use"

```bash
# Puerto 5001 ocupado
lsof -ti:5001 | xargs kill -9
```

### ERROR: "ModuleNotFoundError"

```bash
# Reinstalar dependencias
pip install -r requirements.txt
```

### ERROR: Import errors

```bash
# Verificar PYTHONPATH
echo $PYTHONPATH

# Debería incluir el directorio del proyecto
export PYTHONPATH=/Users/victormfrancisco/Desktop/PROYECTOS/LexDocsPro-LITE:$PYTHONPATH
```

---

## ✅ Solución Rápida (TL;DR)

```bash
# 1. Matar servidor
killall python

# 2. Reiniciar
cd ~/Desktop/PROYECTOS/LexDocsPro-LITE
python run.py

# 3. En otra terminal, verificar
curl http://localhost:5001/api/health

# 4. Ejecutar tests
./tests/test_master_suite.sh
```

**Tiempo total:** < 30 segundos

---

**Fecha:** 2026-02-04  
**Problema:** Endpoints 404 después de añadir código nuevo  
**Solución:** Reiniciar servidor Flask
