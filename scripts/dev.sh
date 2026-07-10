#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
LOCAL_RUNTIME_DIR="${LOCAL_RUNTIME_DIR:-$ROOT/.local-runtime}"

export DOWNLOAD_DIR="${DOWNLOAD_DIR:-$LOCAL_RUNTIME_DIR/downloads}"
export DATABASE_DIR="${DATABASE_DIR:-$LOCAL_RUNTIME_DIR/data}"
export VITE_BACKEND_URL="${VITE_BACKEND_URL:-http://$BACKEND_HOST:$BACKEND_PORT}"
export CHOKIDAR_USEPOLLING="${CHOKIDAR_USEPOLLING:-true}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    echo "Install dependencies, then run this script again." >&2
    exit 1
  fi
}

run_install_hint() {
  if [[ ! -d "$ROOT/.venv" ]]; then
    echo "Python dependencies are not synced yet. Run: uv sync" >&2
    exit 1
  fi

  if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
    echo "Frontend dependencies are not installed yet. Run: npm install --prefix frontend" >&2
    exit 1
  fi
}

require_command npm
run_install_hint

mkdir -p "$DOWNLOAD_DIR" "$DATABASE_DIR"

if command -v uv >/dev/null 2>&1; then
  BACKEND_CMD=(uv run python main.py web --host "$BACKEND_HOST" --port "$BACKEND_PORT")
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  BACKEND_CMD=("$ROOT/.venv/bin/python" main.py web --host "$BACKEND_HOST" --port "$BACKEND_PORT")
else
  echo "Missing required command: uv" >&2
  echo "Run: uv sync" >&2
  exit 1
fi

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  wait "$BACKEND_PID" 2>/dev/null || true
  wait "$FRONTEND_PID" 2>/dev/null || true
  exit "$exit_code"
}
trap cleanup EXIT INT TERM

echo "Starting Downtify local test app"
echo "Backend:  http://$BACKEND_HOST:$BACKEND_PORT"
echo "Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "Data:     $DATABASE_DIR"
echo "Library:  $DOWNLOAD_DIR"
echo
echo "Press Ctrl+C to stop both servers."
echo

"${BACKEND_CMD[@]}" &
BACKEND_PID=$!

npm run dev --prefix frontend -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

wait -n "$BACKEND_PID" "$FRONTEND_PID"
