#!/usr/bin/env bash
# One-command installer for Linux and macOS.
#
#   curl -fsSL https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/install.sh | bash
#
# It downloads or updates the repository in a standard per-user directory and
# runs the platform installer (installer/linux or installer/macos).
set -euo pipefail

REPO_URL="${LOCAL_YTDLP_REPO_URL:-https://github.com/Llop-Estepari/local-ytdlp.git}"
REPO_ARCHIVE="${LOCAL_YTDLP_ARCHIVE_URL:-https://github.com/Llop-Estepari/local-ytdlp/archive/refs/heads/main.tar.gz}"
BRANCH="${LOCAL_YTDLP_BRANCH:-main}"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\nError: %s\n' "$*" >&2; exit 1; }

case "$(uname -s)" in
  Linux)
    PLATFORM="linux"
    DEFAULT_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/local-ytdlp"
    ;;
  Darwin)
    PLATFORM="macos"
    DEFAULT_DIR="$HOME/Library/Application Support/local-ytdlp"
    ;;
  *)
    fail "Sistema no compatible. Usa installer/linux o installer/macos manualmente."
    ;;
esac

INSTALL_DIR="${LOCAL_YTDLP_INSTALL_DIR:-$DEFAULT_DIR}"

# Allow ./install.sh from a local checkout without cloning again.
SCRIPT_PATH="${BASH_SOURCE[0]:-}"
SCRIPT_DIR=""
if [ -n "$SCRIPT_PATH" ] && [ -f "$SCRIPT_PATH" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
fi
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/installer/$PLATFORM/install.sh" ]; then
  APP_DIR="$SCRIPT_DIR"
else
  APP_DIR="$INSTALL_DIR"
fi

download_to() {
  local url="$1"
  local destination="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$destination"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$destination" "$url"
  else
    fail "Se necesita curl o wget para descargar la aplicación."
  fi
}

download_archive() (
  command -v tar >/dev/null 2>&1 || fail "Se necesita tar para extraer la aplicación."

  local temp_dir
  temp_dir="$(mktemp -d)"
  trap 'rm -rf "$temp_dir"' EXIT

  say "Descargando Local YT-DLP…"
  download_to "$REPO_ARCHIVE" "$temp_dir/repo.tar.gz" \
    || fail "No se pudo descargar el repositorio."
  tar -xzf "$temp_dir/repo.tar.gz" -C "$temp_dir" \
    || fail "No se pudo extraer el repositorio."

  local source_dir
  source_dir="$(find "$temp_dir" -mindepth 1 -maxdepth 1 -type d -print -quit)"
  [ -n "$source_dir" ] || fail "El archivo descargado no contiene el proyecto."

  mkdir -p "$INSTALL_DIR"
  cp -a "$source_dir/." "$INSTALL_DIR/"
)

install_or_update() {
  if [ -d "$INSTALL_DIR/.git" ]; then
    command -v git >/dev/null 2>&1 \
      || fail "La instalación existente usa git, pero git no está disponible."
    say "Actualizando Local YT-DLP…"
    git -C "$INSTALL_DIR" pull --ff-only \
      || fail "No se pudo actualizar. Revisa los cambios locales en $INSTALL_DIR."
    return
  fi

  if [ -d "$INSTALL_DIR" ] && [ -n "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]; then
    if [ -f "$INSTALL_DIR/installer/$PLATFORM/install.sh" ]; then
      say "Usando la instalación existente en $INSTALL_DIR"
      return
    fi
    fail "La carpeta $INSTALL_DIR existe pero no parece una instalación de Local YT-DLP."
  fi

  if command -v git >/dev/null 2>&1; then
    say "Descargando Local YT-DLP…"
    if git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"; then
      return
    fi
    rm -rf "$INSTALL_DIR"
    say "git no pudo clonar el repositorio; usando la descarga directa…"
  fi

  download_archive
}

if [ "$APP_DIR" = "$INSTALL_DIR" ]; then
  install_or_update
fi

INSTALLER="$APP_DIR/installer/$PLATFORM/install.sh"
[ -f "$INSTALLER" ] || fail "No se encontró el instalador para $PLATFORM en $INSTALLER."

say "Iniciando la instalación para $PLATFORM…"
# When the script arrives through a pipe, give the platform installer the
# terminal as stdin so interactive prompts (sudo, Homebrew) keep working and
# never consume the remaining bootstrap script.
if { : </dev/tty; } 2>/dev/null; then
  exec bash "$INSTALLER" </dev/tty
else
  exec bash "$INSTALLER" </dev/null
fi
