#!/bin/bash

# --- CONFIGURACIÓN ---
URL="http://localhost:5002"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}   DIAGNÓSTICO LEXDOCSPRO ENTERPRISE v3.1         ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Verificar Procesos
echo -n "1. Servidor Flask (Puerto 5002): "
if lsof -Pi :5002 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}ONLINE${NC}"
else
    echo -e "${RED}OFFLINE${NC}"
fi

# 2. Verificar Carpetas Críticas
echo -e "\n2. Estructura de Carpetas:"
folders=("services" "templates" "static/js" "static/css" "lexdocs.db")
for f in "${folders[@]}"; do
    if [ -e "$f" ]; then
        echo -e "   [${GREEN}OK${NC}] $f"
    else
        echo -e "   [${RED}MISSING${NC}] $f"
    fi
done

# 3. Test API Dashboard (KPIs reales)
echo -n -e "\n3. Test API Dashboard (KPIs): "
RESPONSE=$(curl -s $URL/api/dashboard)
if [[ $RESPONSE == *"1.47"* ]]; then
    echo -e "${GREEN}FUNCIONAL (Data OK)${NC}"
else
    echo -e "${RED}ERROR (Sin respuesta)${NC}"
fi

# 4. Test API LexNET (Cálculo de Plazos 2026)
echo -n "4. Test LexNET (Calendario 2026): "
LEX_RESPONSE=$(curl -s $URL/api/lexnet-urgent)
if [[ $LEX_RESPONSE == *"plazo"* ]]; then
    echo -e "${GREEN}OK (Festivos Cargados)${NC}"
else
    echo -e "${RED}ERROR${NC}"
fi

# 5. Verificar Base de Datos SQLite
echo -n "5. Integridad Base de Datos: "
if [ -f "lexdocs.db" ]; then
    TABLES=$(sqlite3 lexdocs.db ".tables")
    if [[ $TABLES == *"user"* ]]; then
        echo -e "${GREEN}OK (Tablas detectadas)${NC}"
    else
        echo -e "${RED}ERROR (BD Vacía)${NC}"
    fi
else
    echo -e "${RED}MISSING${NC}"
fi

# 6. Test IA Cascade (Status)
echo -n "6. Status IA Cascade: "
IA_STATUS=$(curl -s $URL/api/watchdog-status)
if [[ $IA_STATUS == *"status"* ]]; then
    echo -e "${GREEN}LISTA${NC}"
else
    echo -e "${RED}FALLO${NC}"
fi

echo -e "${BLUE}====================================================${NC}"
echo -e "Si todo está en ${GREEN}VERDE${NC}, estamos listos para la Fase 2."
echo -e "${BLUE}====================================================${NC}"
