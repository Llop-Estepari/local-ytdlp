#!/usr/bin/env python3
"""Start Local YT-DLP as a desktop application.

The default mode opens a native window with ``pywebview`` and keeps the local
FastAPI service running in the background. Use ``--browser`` to keep the old
behaviour (open the interface in the default browser).

This is the entrypoint used by the platform launchers (run.sh, run.ps1 and
run.command). It keeps the process in the foreground so closing the window or
Ctrl+C stops everything cleanly, and it never exposes the service beyond the
configured host.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.desktop import (  # noqa: E402
    ensure_console_streams,
    frontend_ready,
    run_browser,
    run_desktop,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-ytdlp",
        description="Descarga contenido multimedia con yt-dlp en una ventana de escritorio.",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Abrir la interfaz en el navegador en lugar de la ventana nativa.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Abrir las herramientas de desarrollo de la ventana nativa.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    ensure_console_streams()
    args = build_parser().parse_args(argv)

    try:
        settings = Settings.load()
    except RuntimeError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        return 1

    if not frontend_ready(settings):
        print(
            "El frontend no está compilado.\n"
            "Vuelve a descargar la aplicación o ejecuta scripts/build-frontend.sh\n"
            "si eres mantenedor y tienes Node.js instalado.",
            file=sys.stderr,
        )
        return 1

    print("Local YT-DLP Downloader")
    print(f"Datos: {settings.app_data_dir}")
    if settings.allow_network:
        print(
            f"Modo red activo en {settings.host}:{settings.port}. "
            "El token es obligatorio.",
            file=sys.stderr,
        )

    if args.browser:
        return run_browser(settings)
    return run_desktop(settings, debug=args.debug)


if __name__ == "__main__":
    raise SystemExit(main())
