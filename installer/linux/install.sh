#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\nError: %s\n' "$*" >&2; exit 1; }

say "Local YT-DLP Downloader · instalación para Linux"

# --- Python -----------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  fail "Python 3 no está instalado. Instálalo con el gestor de paquetes de tu distribución."
fi

PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
  || fail "Se requiere Python 3.10 o superior (detectado $PY_VERSION)."

# pywebview uses the system WebKitGTK through PyGObject, which lives in the
# system Python. The virtual environment must be able to see system packages.
VENV_CFG="backend/.venv/pyvenv.cfg"
if [ -d backend/.venv ] && ! grep -q 'include-system-site-packages = true' "$VENV_CFG" 2>/dev/null; then
  say "Recreando el entorno virtual para acceder a WebKitGTK del sistema…"
  rm -rf backend/.venv
fi

if [ ! -d backend/.venv ]; then
  say "Creando entorno virtual de Python…"
  python3 -m venv --system-site-packages backend/.venv \
    || fail "No se pudo crear el entorno virtual. En Debian/Ubuntu instala python3-venv."
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

say "Compilando la interfaz…"
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
  cat <<'EOF'

Aviso: FFmpeg no está instalado. Es necesario para combinar pistas y convertir audio.
Instálalo con uno de estos comandos y vuelve a iniciar la aplicación:

  Debian / Ubuntu:  sudo apt install ffmpeg
  Fedora:           sudo dnf install ffmpeg
  Arch Linux:       sudo pacman -S ffmpeg
  openSUSE:         sudo zypper install ffmpeg

EOF
else
  printf 'FFmpeg detectado: %s\n' "$(ffmpeg -version 2>/dev/null | head -n 1)"
fi

# --- Ventana nativa (WebKitGTK) --------------------------------------------
if "$VENV_PYTHON" -c 'import gi; gi.require_version("WebKit2", "4.1")' >/dev/null 2>&1; then
  printf 'WebKitGTK detectado (ventana nativa disponible).\n'
else
  cat <<'EOF'

Aviso: no se detectó WebKitGTK 4.1. La ventana nativa no estará disponible y la
aplicación se abrirá en el navegador. Para habilitarla instala:

  Debian / Ubuntu:  sudo apt install python3-gi gir1.2-webkit2-4.1
  Fedora:           sudo dnf install python3-gobject webkit2gtk4.1
  Arch Linux:       sudo pacman -S python-gobject webkit2gtk-4.1
  openSUSE:         sudo zypper install python3-gobject typelib-1_0-WebKit2-4_1

Después vuelve a ejecutar este instalador.

EOF
fi

printf 'yt-dlp detectado: %s\n' "$("$VENV_PYTHON" -m yt_dlp --version 2>/dev/null || echo 'no disponible')"

# --- Lanzador ---------------------------------------------------------------
chmod +x scripts/run.sh scripts/dev.sh run.command

mkdir -p "$HOME/.local/bin"
ln -sf "$ROOT/scripts/run.sh" "$HOME/.local/bin/local-ytdlp"

DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/local-ytdlp.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Local YT-DLP
Comment=Descarga contenido multimedia con yt-dlp
Exec="$ROOT/scripts/run.sh"
Path=$ROOT
Icon=$ROOT/assets/icon.png
Terminal=false
Categories=AudioVideo;Network;
StartupNotify=true
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

say "Instalación completada"
echo "Inicia la aplicación desde el menú «Local YT-DLP» o ejecutando:"
echo "  $ROOT/scripts/run.sh"
echo
echo "Si ~/.local/bin no está en tu PATH, añade esta línea a tu ~/.bashrc o ~/.zshrc:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
