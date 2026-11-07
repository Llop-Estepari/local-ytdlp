from __future__ import annotations

import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app
from app.services.downloader import FINAL_STATUSES

pytestmark = pytest.mark.integration

if os.environ.get("RUN_INTEGRATION") != "1":
    pytest.skip(
        "Define RUN_INTEGRATION=1 para ejecutar las pruebas reales de descarga.",
        allow_module_level=True,
    )


def _wait_for_final(
    client: TestClient, download_id: str, timeout: float = 180
) -> dict:
    deadline = time.monotonic() + timeout
    state: dict = {}
    while time.monotonic() < deadline:
        response = client.get(f"/api/downloads/{download_id}")
        assert response.status_code == 200
        state = response.json()
        if state["status"] in FINAL_STATUSES:
            return state
        time.sleep(0.25)
    raise AssertionError(f"La descarga no terminó a tiempo: {state}")


def test_real_analyze_youtube(settings: Settings) -> None:
    app = create_app(settings)
    with TestClient(app) as client:
        client.headers["X-API-Token"] = settings.token
        response = client.post(
            "/api/analyze",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["title"]
        assert payload["formats"]
        assert any(item["id"] == "mp4" for item in payload["formats"])


PLAYLIST_URL = "https://www.youtube.com/@jawed/videos"


def test_real_analyze_playlist(settings: Settings) -> None:
    app = create_app(settings)
    with TestClient(app) as client:
        client.headers["X-API-Token"] = settings.token
        response = client.post(
            "/api/analyze", json={"url": PLAYLIST_URL}
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["kind"] == "playlist"
        assert payload["entry_count"] >= 1
        assert payload["entries"]
        assert any(item["id"] == "mp3" for item in payload["formats"])


def test_real_playlist_download(settings: Settings) -> None:
    app = create_app(settings)
    with TestClient(app) as client:
        client.headers["X-API-Token"] = settings.token
        analyze = client.post("/api/analyze", json={"url": PLAYLIST_URL})
        assert analyze.status_code == 200, analyze.text
        info = analyze.json()

        response = client.post(
            "/api/downloads",
            json={
                "url": PLAYLIST_URL,
                "format": "mp3",
                "quality": "128",
                "destination": str(settings.allowed_roots[0]),
                "playlist": True,
                "playlist_count": info["entry_count"],
            },
        )
        assert response.status_code == 201, response.text
        state = _wait_for_final(client, response.json()["id"])

        assert state["status"] == "completed", state
        assert state["playlist"] is True
        assert state["file_count"] >= 1
        assert state["playlist_index"] == info["entry_count"]
        assert state["playlist_count"] == info["entry_count"]
        assert state["filename"].startswith("001 - ")
        filepath = Path(state["filepath"])
        assert filepath.is_file()
        assert filepath.suffix == ".mp3"
        assert filepath.stat().st_size > 0


def test_real_playlist_item_download(settings: Settings) -> None:
    app = create_app(settings)
    with TestClient(app) as client:
        client.headers["X-API-Token"] = settings.token
        response = client.post(
            "/api/downloads",
            json={
                "url": PLAYLIST_URL,
                "format": "mp3",
                "quality": "128",
                "destination": str(settings.allowed_roots[0]),
                "playlist_item": 1,
            },
        )
        assert response.status_code == 201, response.text
        state = _wait_for_final(client, response.json()["id"])

        assert state["status"] == "completed", state
        assert state["playlist"] is False
        assert state["file_count"] == 1
        assert not state["filename"].startswith("001 - ")
        assert state["filename"].endswith(".mp3")
        filepath = Path(state["filepath"])
        assert filepath.is_file()
        assert filepath.stat().st_size > 0


def test_real_download_and_websocket(settings: Settings) -> None:
    app = create_app(settings)
    with TestClient(app) as client:
        client.headers["X-API-Token"] = settings.token
        response = client.post(
            "/api/downloads",
            json={
                "url": "https://download.samplelib.com/mp4/sample-5s.mp4",
                "format": "mp4",
                "quality": "best",
                "destination": str(settings.allowed_roots[0]),
            },
        )
        assert response.status_code == 201, response.text
        download_id = response.json()["id"]

        with client.websocket_connect(
            f"/ws/downloads/{download_id}",
            subprotocols=["local-ytdlp", settings.token],
        ) as websocket:
            state = websocket.receive_json()
            while state["status"] not in FINAL_STATUSES:
                state = websocket.receive_json()

        assert state["status"] == "completed", state
        assert state["filename"]
        filepath = Path(state["filepath"])
        assert filepath.is_file()
        assert filepath.parent == settings.allowed_roots[0]
        assert filepath.stat().st_size > 0


class _SlowHandler(BaseHTTPRequestHandler):
    total = 8 * 1024 * 1024
    chunk = 32 * 1024

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(self.total))
        self.end_headers()
        remaining = self.total
        try:
            while remaining > 0:
                size = min(self.chunk, remaining)
                self.wfile.write(b"0" * size)
                self.wfile.flush()
                remaining -= size
                time.sleep(0.02)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args) -> None:
        return


def test_cancel_real_subprocess(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _SlowHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    async def allow_local(url: str) -> str:
        return url

    monkeypatch.setattr("app.services.downloader.validate_media_url", allow_local)

    app = create_app(settings)
    try:
        with TestClient(app) as client:
            client.headers["X-API-Token"] = settings.token
            response = client.post(
                "/api/downloads",
                json={
                    "url": f"http://127.0.0.1:{port}/slow.mp4",
                    "format": "best",
                    "quality": "best",
                    "destination": str(settings.allowed_roots[0]),
                },
            )
            assert response.status_code == 201, response.text
            download_id = response.json()["id"]

            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                state = client.get(f"/api/downloads/{download_id}").json()
                if state["status"] in {"downloading", "processing"}:
                    break
                time.sleep(0.1)

            time.sleep(0.5)
            cancel = client.post(f"/api/downloads/{download_id}/cancel")
            assert cancel.status_code == 200
            state = cancel.json()
            assert state["status"] == "cancelled", state

            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if not any(settings.temp_dir.glob("*")):
                    break
                time.sleep(0.1)
            assert not any(settings.temp_dir.glob("*"))
            assert not any(settings.allowed_roots[0].glob("*.part"))
    finally:
        server.shutdown()
        server.server_close()
