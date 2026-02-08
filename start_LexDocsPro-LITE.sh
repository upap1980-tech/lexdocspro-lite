#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="LexDocsPro-LITE"
PROJECT_DIR="/Users/victormfrancisco/Desktop/PROYECTOS/LexDocsPro-LITE"
BACKEND_PORT="5002"
FRONTEND_PORT="5174"

function get_local_ip() {
  local ip=""
  if command -v ipconfig >/dev/null 2>&1; then
    ip=$(ipconfig getifaddr en0 2>/dev/null || true)
    if [[ -z "$ip" ]]; then ip=$(ipconfig getifaddr en1 2>/dev/null || true); fi
  fi
  if [[ -z "$ip" ]] && command -v hostname >/dev/null 2>&1; then
    ip=$(hostname -I 2>/dev/null | awk '{print $1}' || true)
  fi
  echo "$ip"
}

LOCAL_IP="$(get_local_ip)"

function echo_title() {
  echo -e "\033]0;$1\007"
}

function ensure_python() {
  local py=""
  if command -v python3.12 >/dev/null 2>&1; then py="python3.12"; 
  elif command -v python3.11 >/dev/null 2>&1; then py="python3.11"; 
  elif command -v python3.10 >/dev/null 2>&1; then py="python3.10"; 
  elif command -v python3.9 >/dev/null 2>&1; then py="python3.9"; 
  elif command -v python3 >/dev/null 2>&1; then py="python3"; 
  fi

  if [[ -z "$py" ]]; then
    if command -v brew >/dev/null 2>&1; then
      echo "[INFO] Installing python@3.12 via Homebrew..."
      brew install python@3.12
      py="python3.12"
    else
      echo "[ERROR] Python not found. Please install Python 3.12 or lower."
      exit 1
    fi
  fi

  local ver
  ver="$($py -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  local major=${ver%%.*}; local minor=${ver##*.}
  if [[ "$major" -gt 3 || ( "$major" -eq 3 && "$minor" -gt 12 ) ]]; then
    echo "[ERROR] Detected Python $ver (>3.12). Use Python 3.12 or lower."
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

function ensure_node_deps() {
  local workdir="$1"
  if [[ -f "$workdir/package.json" ]]; then
    if ! command -v npm >/dev/null 2>&1; then
      echo "[ERROR] npm not found. Please install Node.js."
      return 1
    fi
    if [[ ! -d "$workdir/node_modules" ]]; then
      echo "[INFO] Installing Node deps in $workdir"
      (cd "$workdir" && npm install)
    fi
  fi
}

function run_backend() {
  local backend_file=""
  local backend_dir=""
  if [[ -f "$PROJECT_DIR/backend/run.py" ]]; then backend_file="$PROJECT_DIR/backend/run.py"; backend_dir="$PROJECT_DIR/backend"; fi
  if [[ -z "$backend_file" && -f "$PROJECT_DIR/backend/app.py" ]]; then backend_file="$PROJECT_DIR/backend/app.py"; backend_dir="$PROJECT_DIR/backend"; fi
  if [[ -z "$backend_file" && -f "$PROJECT_DIR/run.py" ]]; then backend_file="$PROJECT_DIR/run.py"; backend_dir="$PROJECT_DIR"; fi
  if [[ -z "$backend_file" && -f "$PROJECT_DIR/app.py" ]]; then backend_file="$PROJECT_DIR/app.py"; backend_dir="$PROJECT_DIR"; fi
  if [[ -z "$backend_file" && -f "$PROJECT_DIR/app_fase7_unificado.py" ]]; then backend_file="$PROJECT_DIR/app_fase7_unificado.py"; backend_dir="$PROJECT_DIR"; fi
  if [[ -z "$backend_file" ]]; then echo "[INFO] Backend not detected for $PROJECT_NAME"; return 0; fi
  local py
  py=$(ensure_python)
  local reqfile=""
  if [[ -f "$backend_dir/requirements.txt" ]]; then reqfile="$backend_dir/requirements.txt"; elif [[ -f "$PROJECT_DIR/requirements.txt" ]]; then reqfile="$PROJECT_DIR/requirements.txt"; fi
  ensure_venv "$backend_dir" "$reqfile" "$py"
  echo_title "$PROJECT_NAME backend :$BACKEND_PORT"
  echo "[INFO] Starting backend: $backend_file (port $BACKEND_PORT)"
  export HOST="0.0.0.0"
  export HOST_DISPLAY="${LOCAL_IP:-127.0.0.1}"
  export FLASK_RUN_HOST="0.0.0.0"
  export FLASK_PORT="$BACKEND_PORT"
  export PORT="$BACKEND_PORT"
  (cd "$backend_dir" && python "$(basename "$backend_file")")
}


function run_frontend() {
  local frontend_dir=""
  if [[ -f "$PROJECT_DIR/frontend/package.json" ]]; then frontend_dir="$PROJECT_DIR/frontend"; elif [[ -f "$PROJECT_DIR/package.json" ]]; then frontend_dir="$PROJECT_DIR"; fi
  if [[ -z "$frontend_dir" ]]; then echo "[INFO] Frontend not detected for $PROJECT_NAME"; return 0; fi
  ensure_node_deps "$frontend_dir"
  echo_title "$PROJECT_NAME frontend :$FRONTEND_PORT"
  echo "[INFO] Starting frontend in $frontend_dir (port $FRONTEND_PORT)"
  export VITE_HOST="0.0.0.0"
  export VITE_PORT="$FRONTEND_PORT"
  if [[ -z "${VITE_API_URL-}" && -n "${LOCAL_IP-}" ]]; then
    export VITE_API_URL="http://${LOCAL_IP}:${BACKEND_PORT}"
  fi
  if [[ -z "${VITE_WS_URL-}" && -n "${LOCAL_IP-}" ]]; then
    export VITE_WS_URL="ws://${LOCAL_IP}:${BACKEND_PORT}"
  fi
  (cd "$frontend_dir" && npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT")
}


function open_terminal_tab() {
  local label="$1"
  local cmd="$2"
  /usr/bin/osascript <<OSA
  tell application "Terminal"
    activate
    do script "cd '$PROJECT_DIR' ; $cmd"
  end tell
OSA
}

function start_all() {
  if [[ -n "${TMUX-}" ]]; then
    tmux new-window -n "${PROJECT_NAME}-backend:${BACKEND_PORT}" "cd '$PROJECT_DIR' && bash -lc 'source $0 __backend'"
    tmux new-window -n "${PROJECT_NAME}-frontend:${FRONTEND_PORT}" "cd '$PROJECT_DIR' && bash -lc 'source $0 __frontend'"
    return
  fi

  open_terminal_tab "${PROJECT_NAME}-backend" "bash -lc 'source $0 __backend'"
  open_terminal_tab "${PROJECT_NAME}-frontend" "bash -lc 'source $0 __frontend'"
}

if [[ "${1-}" == "__backend" ]]; then
  run_backend
  exit 0
fi

if [[ "${1-}" == "__frontend" ]]; then
  run_frontend
  exit 0
fi

start_all
