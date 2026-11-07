#!/usr/bin/env python3
"""Start the local service and open the browser.

This is the entrypoint used by the platform launchers (run.sh, run.ps1 and
run.command). It keeps the process in the foreground so Ctrl+C stops it
cleanly, and it never exposes the service beyond the configured host.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.factory import create_app  # noqa: E402


def health_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/api/health"


def is_running(port: int) -> bool:
    try:
        with urllib.request.urlopen(health_url(port), timeout=1.5) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("status") == "ok"
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return False


def port_is_free(host: str, port: int) -> bool:
    bind_host = "0.0.0.0" if host in {"0.0.0.0", "::", ""} else host
    family = socket.AF_INET6 if ":" in bind_host and bind_host != "0.0.0.0" else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((bind_host, port))
        except OSError:
            return False
    return True


def open_browser_when_ready(url: str, port: int, timeout: float = 45.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_running(port):
            try:
                webbrowser.open(url)
            except Exception:
                pass
            return
        time.sleep(0.25)


def main() -> int:
    try:
        settings = Settings.load()
    except RuntimeError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        return 1

    if is_running(settings.port):
        url = f"http://127.0.0.1:{settings.port}"
        print(f"La aplicación ya está en ejecución: {url}")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return 0

    if not port_is_free(settings.host, settings.port):
        print(
            f"El puerto {settings.port} está ocupado por otro programa.\n"
            "Cierra ese programa o define LOCAL_YTDLP_PORT con otro puerto.",
            file=sys.stderr,
        )
        return 1

    index = settings.frontend_dir / "index.html"
    if not index.is_file():
        print(
            "El frontend no está compilado.\n"
            "Ejecuta el instalador de la aplicación o, dentro de frontend/:\n"
            "  npm install && npm run build",
            file=sys.stderr,
        )
        return 1

    url = f"http://127.0.0.1:{settings.port}"
    print("Local YT-DLP Downloader")
    print(f"Interfaz: {url}")
    print(f"Datos:    {settings.app_data_dir}")
    if settings.allow_network:
        print(
            f"Modo red activo en {settings.host}:{settings.port}. "
            "El token es obligatorio.",
            file=sys.stderr,
        )
    print("Pulsa Ctrl+C para detener la aplicación.\n")

    threading.Thread(
        target=open_browser_when_ready,
        args=(url, settings.port),
        daemon=True,
    ).start()

    import uvicorn

    try:
        uvicorn.run(
            create_app(settings),
            host=settings.host,
            port=settings.port,
            log_level="info",
            access_log=False,
        )
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
