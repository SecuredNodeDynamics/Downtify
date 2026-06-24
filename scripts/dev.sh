#!/usr/bin/env bash
# Start local backend + Vite frontend for development.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p docker/downloads docker/data

export DOWNLOAD_DIR="${DOWNLOAD_DIR:-$ROOT/docker/downloads}"
export DATABASE_DIR="${DATABASE_DIR:-$ROOT/docker/data}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:5173"
echo "Data:     $DATABASE_DIR"
echo "Library:  $DOWNLOAD_DIR"

uv run python main.py &
BACKEND_PID=$!

npm run dev --prefix frontend &
FRONTEND_PID=$!

wait
