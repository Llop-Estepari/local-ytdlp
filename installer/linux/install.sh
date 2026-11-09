#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\nError: %s\n' "$*" >&2; exit 1; }
warn() { printf '\nAviso: %b\n\n' "$*" >&2; }

say "Local YT-DLP Downloader · instalación para Linux"

# --- Dependencias del sistema ----------------------------------------------
PM=""
SUDO=()

detect_package_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    PM="apt"
  elif command -v dnf >/dev/null 2>&1; then
    PM="dnf"
  elif command -v pacman >/dev/null 2>&1; then
    PM="pacman"
  elif command -v zypper >/dev/null 2>&1; then
    PM="zypper"
  else
    fail "No se detectó un gestor de paquetes compatible (apt, dnf, pacman o zypper)."
  fi
}

setup_privileges() {
  if [ "$(id -u)" -eq 0 ]; then
    SUDO=()
  elif command -v sudo >/dev/null 2>&1; then
    SUDO=(sudo)
  else
    fail "Se necesitan permisos de administrador y 'sudo' no está disponible."
  fi
}

pm_update() {
  case "$PM" in
    apt) "${SUDO[@]}" apt-get update -y ;;
    dnf) "${SUDO[@]}" dnf -y makecache ;;
    pacman) "${SUDO[@]}" pacman -Sy --noconfirm ;;
    zypper) "${SUDO[@]}" zypper --non-interactive refresh ;;
  esac
}

pm_install() {
  case "$PM" in
    apt) "${SUDO[@]}" apt-get install -y "$@" ;;
    dnf) "${SUDO[@]}" dnf install -y "$@" ;;
    pacman) "${SUDO[@]}" pacman -S --needed --noconfirm "$@" ;;
    zypper) "${SUDO[@]}" zypper --non-interactive install "$@" ;;
  esac
}

install_python() {
  case "$PM" in
    apt) pm_install python3 python3-venv ;;
    dnf) pm_install python3 python3-pip ;;
    pacman) pm_install python python-pip ;;
    zypper) pm_install python3 python3-pip ;;
  esac
}

install_webkit() {
  case "$PM" in
    apt) pm_install python3-gi gir1.2-webkit2-4.1 ;;
    dnf) pm_install python3-gobject webkit2gtk4.1 ;;
    pacman) pm_install python-gobject webkit2gtk-4.1 ;;
    zypper) pm_install python3-gobject typelib-1_0-WebKit2-4_1 ;;
  esac
}

install_ffmpeg() {
  pm_install ffmpeg
}

NEED_PYTHON=0
NEED_VENV=0
NEED_WEBKIT=0
NEED_FFMPEG=0

if ! command -v python3 >/dev/null 2>&1; then
  NEED_PYTHON=1
  NEED_VENV=1
  NEED_WEBKIT=1
else
  python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
    || NEED_PYTHON=1
  python3 -c 'import ensurepip' >/dev/null 2>&1 || NEED_VENV=1
  python3 -c 'import gi; gi.require_version("WebKit2", "4.1")' >/dev/null 2>&1 \
    || NEED_WEBKIT=1
fi
command -v ffmpeg >/dev/null 2>&1 || NEED_FFMPEG=1

if [ "$NEED_PYTHON" -eq 1 ] || [ "$NEED_VENV" -eq 1 ] \
  || [ "$NEED_WEBKIT" -eq 1 ] || [ "$NEED_FFMPEG" -eq 1 ]; then
  detect_package_manager
  setup_privileges
  say "Instalando dependencias del sistema (puede pedir tu contraseña)…"
  pm_update || true
  if [ "$NEED_PYTHON" -eq 1 ] || [ "$NEED_VENV" -eq 1 ]; then
    install_python || true
  fi
  if [ "$NEED_WEBKIT" -eq 1 ]; then
    install_webkit || true
  fi
  if [ "$NEED_FFMPEG" -eq 1 ]; then
    install_ffmpeg || true
  fi
fi

if ! command -v python3 >/dev/null 2>&1; then
  fail "No se pudo instalar Python 3. Instálalo manualmente con el gestor de paquetes de tu distribución."
fi

PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
  || fail "Se requiere Python 3.10 o superior (detectado $PY_VERSION)."

if ! python3 -c 'import ensurepip' >/dev/null 2>&1; then
  fail "El módulo 'venv' de Python no está disponible. En Debian/Ubuntu ejecuta: sudo apt install python3-venv"
fi

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

# --- Interfaz precompilada --------------------------------------------------
if [ ! -f frontend/out/index.html ]; then
  fail "Falta frontend/out/index.html. Ejecuta scripts/build-frontend.sh en el repositorio o vuelve a descargar la aplicación."
fi

# --- FFmpeg -----------------------------------------------------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  warn "FFmpeg no está instalado. Es necesario para combinar pistas y convertir audio.\n\nInstálalo con uno de estos comandos y vuelve a iniciar la aplicación:\n\n  Debian / Ubuntu:  sudo apt install ffmpeg\n  Fedora:           sudo dnf install ffmpeg\n  Arch Linux:       sudo pacman -S ffmpeg\n  openSUSE:         sudo zypper install ffmpeg"
else
  printf 'FFmpeg detectado: %s\n' "$(ffmpeg -version 2>/dev/null | head -n 1)"
fi

# --- Ventana nativa (WebKitGTK) --------------------------------------------
if "$VENV_PYTHON" -c 'import gi; gi.require_version("WebKit2", "4.1")' >/dev/null 2>&1; then
  printf 'WebKitGTK detectado (ventana nativa disponible).\n'
else
  warn "No se detectó WebKitGTK 4.1. La ventana nativa no estará disponible y la aplicación se abrirá en el navegador.\n\nPara habilitarla instala:\n\n  Debian / Ubuntu:  sudo apt install python3-gi gir1.2-webkit2-4.1\n  Fedora:           sudo dnf install python3-gobject webkit2gtk4.1\n  Arch Linux:       sudo pacman -S python-gobject webkit2gtk-4.1\n  openSUSE:         sudo zypper install python3-gobject typelib-1_0-WebKit2-4_1\n\nDespués vuelve a ejecutar este instalador."
fi

printf 'yt-dlp detectado: %s\n' "$("$VENV_PYTHON" -m yt_dlp --version 2>/dev/null || echo 'no disponible')"

# --- Lanzador ---------------------------------------------------------------
chmod +x scripts/run.sh scripts/dev.sh scripts/build-frontend.sh run.command

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
