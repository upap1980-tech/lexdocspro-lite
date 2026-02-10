#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="LexDocsPro-LITE"
PROJECT_DIR="/Users/victormfrancisco/Desktop/PROYECTOS/LexDocsPro-LITE"

PORTS_REGISTRY="/Users/victormfrancisco/Desktop/PROYECTOS/LANZADORES/ports_registry.sh"
if [[ ! -f "$PORTS_REGISTRY" ]]; then
  echo "[ERROR] Missing ports registry: $PORTS_REGISTRY"
  exit 1
fi
source "$PORTS_REGISTRY"
if ! get_project_ports "$PROJECT_NAME" BACKEND_PORT FRONTEND_PORT; then
  echo "[ERROR] No fixed ports configured for project: $PROJECT_NAME"
  exit 1
fi
readonly BACKEND_PORT FRONTEND_PORT
HOST_BIND="${HOST_BIND:-0.0.0.0}"

function echo_title() { echo -e "\033]0;$1\007"; }

function ensure_python() {
  local py=""
  if command -v python3.12 >/dev/null 2>&1; then py="python3.12";
  elif command -v python3.11 >/dev/null 2>&1; then py="python3.11";
  elif command -v python3.10 >/dev/null 2>&1; then py="python3.10";
  elif command -v python3.9 >/dev/null 2>&1; then py="python3.9";
  elif command -v python3 >/dev/null 2>&1; then py="python3";
  fi
  if [[ -z "$py" ]]; then
    echo "[ERROR] Python not found. Install Python 3.12 or lower."
    exit 1
  fi
  local ver
  ver="$($py -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  local major=${ver%%.*}; local minor=${ver##*.}
  if [[ "$major" -gt 3 || ( "$major" -eq 3 && "$minor" -gt 12 ) ]]; then
    echo "[ERROR] Detected Python $ver (>3.12). Use 3.12 or lower."
    exit 1
  fi
  echo "$py"
}

function ensure_venv() {
  local workdir="$1"
  local reqfile="$2"
  local py="$3"
  local venv_dir=""
  if [[ -d "$workdir/.venv312" ]]; then
    venv_dir="$workdir/.venv312"
  else
    venv_dir="$workdir/.venv"
  fi
  if [[ ! -d "$venv_dir" ]]; then
    echo "[INFO] Creating venv at $venv_dir"
    "$py" -m venv "$venv_dir"
  fi
  source "$venv_dir/bin/activate"
  python -m pip install --upgrade pip >/dev/null 2>&1 || true
  if [[ -n "$reqfile" && -f "$reqfile" ]]; then
    echo "[INFO] Installing Python deps from $reqfile"
    pip install -r "$reqfile"
  fi
}

function check_env_file() {
  if [[ ! -f "$PROJECT_DIR/.env" ]]; then
    echo "[WARN] .env not found. Copying from .env.example"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  fi
}

function check_ai_keys() {
  local ok=0
  if [[ -n "${OLLAMA_BASE_URL:-}" || -n "${OLLAMA_URL:-}" ]]; then ok=1; fi
  if [[ -n "${GROQ_API_KEY:-}" || -n "${OPENAI_API_KEY:-}" || -n "${PERPLEXITY_API_KEY:-}" || -n "${GEMINI_API_KEY:-}" || -n "${ANTHROPIC_API_KEY:-}" ]]; then ok=1; fi
  if [[ "$ok" -eq 0 ]]; then
    echo "[WARN] No IA provider configured (OLLAMA_* or API keys). IA will run in degraded mode."
  fi
}

function check_ollama() {
  if [[ -z "${OLLAMA_BASE_URL:-}" ]]; then
    echo "[WARN] OLLAMA_BASE_URL no configurado. IA local no arrancará."
    echo "       Configura OLLAMA_BASE_URL (p.ej. http://localhost:11434) y levanta con: ollama serve"
    echo "       Modelos sugeridos: lexdocs-legal-pro (instala con: ollama pull lexdocs-legal-pro)"
  fi
}

function check_smtp() {
  if [[ -z "${SMTP_HOST:-}" || -z "${SMTP_USER:-}" || -z "${SMTP_PASS:-}" ]]; then
    echo "[WARN] SMTP incompleto (SMTP_HOST/USER/PASS). Email Alerts quedará en modo simulado."
    echo "       Rellena SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM; TLS recomendado (SMTP_USE_TLS=true)."
  fi
}

function check_banking() {
  if [[ -z "${BANKING_GOCARDLESS_SECRET_ID:-}" || -z "${BANKING_GOCARDLESS_SECRET_KEY:-}" ]]; then
    echo "[WARN] Banking sin credenciales GoCardless. /api/banking/* responderá configured:false."
    echo "       Necesitas BANKING_GOCARDLESS_SECRET_ID y BANKING_GOCARDLESS_SECRET_KEY (+ BANKING_ACCOUNT_IDS opcional)."
  fi
}

function check_email() {
  if [[ -z "${SMTP_HOST:-}" || -z "${SMTP_USER:-}" || -z "${SMTP_PASS:-}" ]]; then
    echo "[WARN] SMTP not fully configured. Email Alerts may fail."
  fi
}

function check_certificates() {
  local cert_dir="$HOME/Desktop/CERTIFICADOS"
  if [[ ! -d "$cert_dir" ]]; then
    echo "[WARN] Certificate folder not found: $cert_dir"
    return 0
  fi
  if ! ls "$cert_dir"/*.p12 >/dev/null 2>&1; then
    echo "[WARN] No .p12 certificates found in $cert_dir"
  fi
}

function run_backend() {
  local backend_file="$PROJECT_DIR/run.py"
  local reqfile="$PROJECT_DIR/requirements.txt"
  local py
  py=$(ensure_python)
  ensure_venv "$PROJECT_DIR" "$reqfile" "$py"
  check_env_file
  source "$PROJECT_DIR/.env" 2>/dev/null || true
  check_ai_keys
  check_ollama
  check_smtp
  check_banking
  check_email
  check_certificates
  # Abrir login en Safari en paralelo (no bloquea). Espera breve para que Flask arranque.
  (sleep 2 && open -a "Safari" "http://localhost:5002/login") >/dev/null 2>&1 &
  echo_title "$PROJECT_NAME backend :$BACKEND_PORT"
  echo "[INFO] Starting backend: $backend_file (host $HOST_BIND port $BACKEND_PORT)"
  export HOST="$HOST_BIND"
  export FLASK_RUN_HOST="$HOST_BIND"
  export FLASK_PORT="$BACKEND_PORT"
  export PORT="$BACKEND_PORT"
  export HOST="$HOST_BIND"
  (cd "$PROJECT_DIR" && python "$(basename "$backend_file")")
}

run_backend
