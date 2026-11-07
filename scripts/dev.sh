#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/backend/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "No se encontró el entorno de Python." >&2
  echo "Ejecuta el instalador o crea el entorno con:" >&2
  echo "  cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt" >&2
  exit 1
fi

cleanup() {
  if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

cd "$ROOT"
"$PYTHON" -m uvicorn app.main:app \
  --app-dir backend \
  --host 127.0.0.1 \
  --port 8765 \
  --reload \
  --reload-dir backend/app &
BACKEND_PID=$!

echo "API:    http://127.0.0.1:8765"
echo "Interfaz: http://127.0.0.1:3000"
echo

cd frontend
npm run dev
