#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\nError: %s\n' "$*" >&2; exit 1; }

say "Local YT-DLP Downloader · instalación para macOS"

# --- Python -----------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  fail "Python 3 no está instalado. Instálalo desde https://www.python.org/downloads/ o con Homebrew."
fi

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
  || fail "Se requiere Python 3.10 o superior (detectado $(python3 -V 2>&1))."

if [ ! -d backend/.venv ]; then
  say "Creando entorno virtual de Python…"
  python3 -m venv backend/.venv
fi

VENV_PYTHON="$ROOT/backend/.venv/bin/python"

say "Instalando dependencias de Python (FastAPI, yt-dlp)…"
"$VENV_PYTHON" -m pip install --upgrade pip --quiet
"$VENV_PYTHON" -m pip install -r backend/requirements.txt --quiet

# --- Node / frontend --------------------------------------------------------
if ! command -v npm >/dev/null 2>&1 || ! command -v node >/dev/null 2>&1; then
  fail "Node.js y npm son necesarios para compilar la interfaz. Instala Node.js 20 o superior."
fi

NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$NODE_MAJOR" -lt 20 ]; then
  fail "Se requiere Node.js 20 o superior (detectado $(node --version))."
fi

say "Compilando la interfaz web…"
cd frontend
if [ -f package-lock.json ]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi
npm run build
cd "$ROOT"

# --- FFmpeg -----------------------------------------------------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    say "Instalando FFmpeg con Homebrew…"
    brew install ffmpeg || fail "No se pudo instalar FFmpeg. Ejecuta: brew install ffmpeg"
  else
    cat <<'EOF'

Aviso: FFmpeg no está instalado. Es necesario para combinar pistas y convertir audio.
Instálalo con Homebrew (https://brew.sh):

  brew install ffmpeg

Después vuelve a iniciar la aplicación.

EOF
  fi
else
  printf 'FFmpeg detectado: %s\n' "$(ffmpeg -version 2>/dev/null | head -n 1)"
fi

printf 'yt-dlp detectado: %s\n' "$("$VENV_PYTHON" -m yt_dlp --version 2>/dev/null || echo 'no disponible')"

# --- Lanzador ---------------------------------------------------------------
chmod +x scripts/run.sh scripts/dev.sh run.command

APP_DIR="$HOME/Applications"
mkdir -p "$APP_DIR"
LAUNCHER="$APP_DIR/Local YT-DLP.command"
cat > "$LAUNCHER" <<EOF
#!/bin/bash
exec "$ROOT/scripts/run.sh" "\$@"
EOF
chmod +x "$LAUNCHER"

say "Instalación completada"
echo "Abre «Local YT-DLP» desde tu carpeta Aplicaciones o ejecuta:"
echo "  $ROOT/scripts/run.sh"
echo
echo "La primera vez, macOS puede pedir permiso para abrir el lanzador:"
echo "haz clic derecho sobre «Local YT-DLP.command» y elige «Abrir»."
