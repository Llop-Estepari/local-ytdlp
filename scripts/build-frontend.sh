#!/usr/bin/env bash
# Rebuild the static interface that ships in frontend/out.
# Only maintainers need this script: end users never need Node.js or npm.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND="$ROOT/frontend"

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Node.js 20+ y npm son necesarios solo para regenerar la interfaz." >&2
  exit 1
fi

NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$NODE_MAJOR" -lt 20 ]; then
  echo "Se requiere Node.js 20 o superior (detectado $(node --version))." >&2
  exit 1
fi

cd "$FRONTEND"
rm -rf out
if [ -f package-lock.json ]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi
npm run build

echo
echo "Interfaz compilada en frontend/out."
echo "Recuerda hacer commit de frontend/out para que los instaladores la incluyan."
