"""Native desktop mode.

The application keeps a loopback HTTP server because the interface talks to
the backend over REST and WebSocket. ``pywebview`` renders the static Next.js
build inside a native window (WebKitGTK on Linux, WebView2 on Windows and
WKWebView on macOS), so the user never has to open a browser.

The server always listens on the loopback interface. The window loads the same
origin that serves the API, which keeps the existing token, origin and CSP
protections intact.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass, field
from typing import Any

from .core.config import Settings
from .factory import create_app

WINDOW_TITLE = "Local YT-DLP"
WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 820
WINDOW_MIN_SIZE = (760, 560)
WINDOW_BACKGROUND = "#0a0a0a"

# Health checks must never go through a system proxy.
_LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def ensure_console_streams() -> None:
    """Keep printing safe under Windows ``pythonw.exe``.

    ``pythonw`` does not attach a console, so ``sys.stdout`` and ``sys.stderr``
    can be ``None``. Sending output to the null device avoids crashes; the
    backend still writes its own log file.
    """

    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def _print(*args: Any, file: Any = None, **kwargs: Any) -> None:
    """Print safely even if the process has no console attached."""

    stream = file if file is not None else sys.stdout
    if stream is not None:
        print(*args, file=stream, **kwargs)


def frontend_ready(settings: Settings) -> bool:
    return (settings.frontend_dir / "index.html").is_file()


def health_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/api/health"


def is_running(port: int, timeout: float = 1.5) -> bool:
    """Return True when another instance of the service is already listening."""

    try:
        with _LOCAL_OPENER.open(health_url(port), timeout=timeout) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("status") == "ok"
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return False


def port_is_free(host: str, port: int) -> bool:
    bind_host = "0.0.0.0" if host in {"0.0.0.0", "::", ""} else host
    family = (
        socket.AF_INET6
        if ":" in bind_host and bind_host != "0.0.0.0"
        else socket.AF_INET
    )
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((bind_host, port))
        except OSError:
            return False
    return True


@dataclass(slots=True)
class ServerHandle:
    """A uvicorn server running in a background thread."""

    server: Any
    thread: threading.Thread
    errors: list[BaseException] = field(default_factory=list)

    def stop(self) -> None:
        self.server.should_exit = True
        if self.thread.is_alive():
            self.thread.join(timeout=10)


def start_background_server(settings: Settings) -> ServerHandle:
    import uvicorn

    app = create_app(settings)
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    errors: list[BaseException] = []

    def run() -> None:
        try:
            server.run()
        except BaseException as exc:  # pragma: no cover - platform dependent
            errors.append(exc)

    thread = threading.Thread(
        target=run,
        name="local-ytdlp-server",
        daemon=True,
    )
    thread.start()
    return ServerHandle(server=server, thread=thread, errors=errors)


def wait_until_ready(handle: ServerHandle, timeout: float = 45.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if handle.errors:
            raise RuntimeError(str(handle.errors[0]))
        if handle.server.started:
            return
        if not handle.thread.is_alive():
            raise RuntimeError("El servicio local se detuvo antes de estar listo.")
        time.sleep(0.15)
    raise TimeoutError("El servicio local no respondió a tiempo.")


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


def _select_gui() -> str | None:
    """Prefer GTK on Linux when WebKitGTK is available.

    Without an explicit backend, pywebview probes Qt first and prints a noisy
    traceback when Qt is not installed. Returning ``None`` keeps pywebview's
    automatic selection on every other platform.
    """

    if not sys.platform.startswith("linux"):
        return None
    try:
        import gi

        gi.require_version("WebKit2", "4.1")
    except (ImportError, ValueError):
        return None
    return "gtk"


def _open_native_window(settings: Settings, url: str, debug: bool) -> None:
    import webview

    storage = settings.app_data_dir / "webview"
    storage.mkdir(parents=True, exist_ok=True)
    icon = settings.project_root / "assets" / "icon.png"

    webview.create_window(
        WINDOW_TITLE,
        url=url,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=WINDOW_MIN_SIZE,
        background_color=WINDOW_BACKGROUND,
        text_select=True,
    )
    webview.start(
        gui=_select_gui(),
        debug=debug,
        private_mode=False,
        storage_path=str(storage),
        icon=str(icon) if icon.is_file() else None,
    )


def run_desktop(settings: Settings, *, debug: bool = False) -> int:
    """Open the native application window, starting the local service if needed."""

    ensure_console_streams()
    if not frontend_ready(settings):
        _print(
            "El frontend no está compilado.\n"
            "Vuelve a descargar la aplicación o ejecuta scripts/build-frontend.sh\n"
            "si eres mantenedor y tienes Node.js instalado.",
            file=sys.stderr,
        )
        return 1

    try:
        import webview  # noqa: F401
    except ImportError:
        _print(
            "pywebview no está instalado; se abrirá la interfaz en el navegador.\n"
            "Para usar la ventana nativa ejecuta:\n"
            "  backend/.venv/bin/pip install -r backend/requirements.txt",
            file=sys.stderr,
        )
        return run_browser(settings)

    handle: ServerHandle | None = None
    if is_running(settings.port):
        url = f"http://127.0.0.1:{settings.port}"
        _print(f"Usando la instancia ya en ejecución: {url}")
    else:
        if not port_is_free(settings.host, settings.port):
            _print(
                f"El puerto {settings.port} está ocupado por otro programa.\n"
                "Cierra ese programa o define LOCAL_YTDLP_PORT con otro puerto.",
                file=sys.stderr,
            )
            return 1

        handle = start_background_server(settings)
        try:
            wait_until_ready(handle)
        except Exception as exc:
            handle.stop()
            _print(f"No se pudo iniciar el servicio local: {exc}", file=sys.stderr)
            return 1
        url = f"http://127.0.0.1:{settings.port}"

    try:
        _open_native_window(settings, url, debug)
    except Exception as exc:
        if handle is not None:
            handle.stop()
        _print(
            f"No se pudo abrir la ventana nativa: {exc}\n"
            "Se abrirá la interfaz en el navegador. Revisa los requisitos de "
            "WebView de tu sistema (WebKitGTK, WebView2 o WKWebView).",
            file=sys.stderr,
        )
        return run_browser(settings)
    finally:
        if handle is not None:
            handle.stop()

    return 0


def run_browser(settings: Settings) -> int:
    """Fallback mode: serve the interface and open it in the default browser."""

    ensure_console_streams()
    if not frontend_ready(settings):
        _print(
            "El frontend no está compilado.\n"
            "Vuelve a descargar la aplicación o ejecuta scripts/build-frontend.sh\n"
            "si eres mantenedor y tienes Node.js instalado.",
            file=sys.stderr,
        )
        return 1

    url = f"http://127.0.0.1:{settings.port}"
    if is_running(settings.port):
        _print(f"La aplicación ya está en ejecución: {url}")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return 0

    if not port_is_free(settings.host, settings.port):
        _print(
            f"El puerto {settings.port} está ocupado por otro programa.\n"
            "Cierra ese programa o define LOCAL_YTDLP_PORT con otro puerto.",
            file=sys.stderr,
        )
        return 1

    _print("Local YT-DLP Downloader")
    _print(f"Interfaz: {url}")
    _print(f"Datos:    {settings.app_data_dir}")
    if settings.allow_network:
        _print(
            f"Modo red activo en {settings.host}:{settings.port}. "
            "El token es obligatorio.",
            file=sys.stderr,
        )
    _print("Pulsa Ctrl+C para detener la aplicación.\n")

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
