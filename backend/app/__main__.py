"""Allow ``python -m app`` to start the desktop application.

Use ``python -m app --browser`` to open the interface in the default browser and
``python -m app --server`` to run only the HTTP service (useful for debugging or
for a headless deployment).
"""

from __future__ import annotations

import argparse
import sys

from .core.config import Settings
from .desktop import run_browser, run_desktop


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app",
        description="Local YT-DLP Downloader",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Abrir la interfaz en el navegador en lugar de la ventana nativa.",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Ejecutar solo el servicio HTTP, sin ventana ni navegador.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Abrir las herramientas de desarrollo de la ventana nativa.",
    )
    args = parser.parse_args(argv)

    try:
        settings = Settings.load()
    except RuntimeError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.server:
        import uvicorn

        from .factory import create_app

        uvicorn.run(
            create_app(settings),
            host=settings.host,
            port=settings.port,
            log_level="info",
        )
        return

    if args.browser:
        raise SystemExit(run_browser(settings))
    raise SystemExit(run_desktop(settings, debug=args.debug))


if __name__ == "__main__":
    main()
