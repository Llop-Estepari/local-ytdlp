#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\nError: %s\n' "$*" >&2; exit 1; }
warn() { printf '\nAviso: %b\n\n' "$*" >&2; }

say "Vidora · instalación para macOS"

# --- Homebrew ---------------------------------------------------------------
load_brew() {
  if command -v brew >/dev/null 2>&1; then
    return 0
  fi
  if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

ensure_homebrew() {
  load_brew
  if command -v brew >/dev/null 2>&1; then
    return 0
  fi
  say "Homebrew no está instalado. Instalándolo automáticamente (puede pedir tu contraseña)…"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
    || fail "No se pudo instalar Homebrew. Instálalo manualmente desde https://brew.sh y vuelve a ejecutar este instalador."
  load_brew
  command -v brew >/dev/null 2>&1 \
    || fail "Homebrew se instaló pero no se pudo cargar en el PATH. Abre una terminal nueva y vuelve a ejecutar este instalador."
}

# --- Python -----------------------------------------------------------------
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PYTHON_BIN="$(command -v python3)"
  fi
fi

if [ -z "$PYTHON_BIN" ]; then
  ensure_homebrew
  say "Instalando Python con Homebrew…"
  brew install python \
    || fail "No se pudo instalar Python con Homebrew. Ejecuta: brew install python"
  load_brew
  PYTHON_BIN="$(brew --prefix)/bin/python3"
fi

"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
  || fail "Se requiere Python 3.10 o superior (detectado $("$PYTHON_BIN" -V 2>&1))."

if [ ! -d backend/.venv ]; then
  say "Creando entorno virtual de Python…"
  "$PYTHON_BIN" -m venv backend/.venv \
    || fail "No se pudo crear el entorno virtual de Python."
fi

VENV_PYTHON="$ROOT/backend/.venv/bin/python"

say "Instalando dependencias de Python (FastAPI, yt-dlp)…"
"$VENV_PYTHON" -m pip install --upgrade pip --quiet
"$VENV_PYTHON" -m pip install -r backend/requirements.txt --quiet

# --- Interfaz precompilada --------------------------------------------------
if [ ! -f frontend/out/index.html ]; then
  fail "Falta frontend/out/index.html. Ejecuta scripts/build-frontend.sh en el repositorio o vuelve a descargar la aplicación."
fi

# --- FFmpeg -----------------------------------------------------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  ensure_homebrew
  say "Instalando FFmpeg con Homebrew…"
  brew install ffmpeg \
    || warn "No se pudo instalar FFmpeg automáticamente. Ejecuta: brew install ffmpeg"
else
  printf 'FFmpeg detectado: %s\n' "$(ffmpeg -version 2>/dev/null | head -n 1)"
fi

printf 'yt-dlp detectado: %s\n' "$("$VENV_PYTHON" -m yt_dlp --version 2>/dev/null || echo 'no disponible')"

# --- Lanzador ---------------------------------------------------------------
chmod +x scripts/run.sh scripts/dev.sh scripts/build-frontend.sh run.command

APP_DIR="$HOME/Applications"
APP_BUNDLE="$APP_DIR/Vidora.app"
mkdir -p "$APP_DIR"
rm -rf "$APP_BUNDLE"
rm -rf "$APP_DIR/Local YT-DLP.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS" "$APP_BUNDLE/Contents/Resources"
if [ -f assets/icon.icns ]; then
  cp assets/icon.icns "$APP_BUNDLE/Contents/Resources/icon.icns"
fi

cat > "$APP_BUNDLE/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>Vidora</string>
  <key>CFBundleDisplayName</key>
  <string>Vidora</string>
  <key>CFBundleIdentifier</key>
  <string>com.vidora.app</string>
  <key>CFBundleVersion</key>
  <string>1.0.0</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0.0</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleExecutable</key>
  <string>launcher</string>
  <key>CFBundleIconFile</key>
  <string>icon.icns</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.15</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
EOF

cat > "$APP_BUNDLE/Contents/MacOS/launcher" <<EOF
#!/bin/bash
exec "$ROOT/backend/.venv/bin/python" "$ROOT/scripts/launch.py" "\$@"
EOF
chmod +x "$APP_BUNDLE/Contents/MacOS/launcher"

say "Instalación completada"
echo "Abre «Vidora» desde tu carpeta Aplicaciones o ejecuta:"
echo "  open \"$APP_BUNDLE\""
echo
echo "La primera vez, macOS puede pedir permiso para abrir la aplicación:"
echo "haz clic derecho sobre «Vidora» y elige «Abrir»."
