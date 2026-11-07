#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/backend/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "No se encontró el entorno de Python de la aplicación." >&2
  echo "Ejecuta primero el instalador: installer/macos/install.sh" >&2
  read -r -n 1 -s -p "Pulsa una tecla para cerrar…"
  exit 1
fi

exec "$PYTHON" "$ROOT/scripts/launch.py" "$@"
