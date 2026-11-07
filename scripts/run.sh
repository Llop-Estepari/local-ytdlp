#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/backend/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "No se encontró el entorno de Python de la aplicación." >&2
  echo "Ejecuta primero el instalador: installer/linux/install.sh" >&2
  exit 1
fi

exec "$PYTHON" "$ROOT/scripts/launch.py" "$@"
