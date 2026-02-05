#!/bin/bash
echo "=== 1. CONTENIDO SERVICES/ ==="
ls -lah services/ 2>/dev/null || echo "services/ no existe"
echo ""

echo "=== 2. GIT STATUS ==="
git status 2>/dev/null || echo "No es repo Git"
echo ""

echo "=== 3. GIT LOG ==="
git log --oneline -15 2>/dev/null || echo "Sin historial"
echo ""

echo "=== 4. RAMAS ==="
git branch -a 2>/dev/null || echo "Sin ramas"
echo ""

echo "=== 5. REMOTES ==="
git remote -v 2>/dev/null || echo "Sin remotes"
echo ""

echo "=== 6. PRIMERAS 30 LÍNEAS RUN.PY ==="
head -30 run.py
echo ""

echo "=== 7. IMPORTS EN RUN.PY ==="
grep "^import \|^from " run.py | head -20
echo ""

echo "=== 8. ARCHIVOS PYTHON EN ROOT ==="
ls -1 *.py 2>/dev/null
echo ""

echo "=== 9. BACKUPS DISPONIBLES ==="
find . -maxdepth 2 -name "*backup*" -o -name "*.bak" 2>/dev/null
