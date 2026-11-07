"""Tests for the native desktop launcher helpers."""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.core.config import Settings
from app.desktop import frontend_ready, is_running, port_is_free, run_desktop


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server API
        payload = json.dumps({"status": "ok"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args: object) -> None:
        pass


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_frontend_ready_checks_index(tmp_path: Path) -> None:
    settings = Settings.for_testing(tmp_path)
    assert not frontend_ready(settings)

    settings.frontend_dir.mkdir(parents=True, exist_ok=True)
    (settings.frontend_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    assert frontend_ready(settings)


def test_is_running_detects_local_health_service() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HealthHandler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert is_running(port)
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_is_running_rejects_free_port() -> None:
    assert not is_running(_free_port(), timeout=0.25)


def test_port_is_free_detects_bound_socket() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
        assert not port_is_free("127.0.0.1", port)


def test_run_desktop_requires_built_frontend(tmp_path: Path, capsys) -> None:
    settings = Settings.for_testing(tmp_path)
    assert run_desktop(settings) == 1
    assert "frontend no está compilado" in capsys.readouterr().err
