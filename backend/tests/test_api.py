from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import Settings
from app.services.tools import ToolUpdateResult


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" in response.headers


def test_session_returns_token_without_auth(client: TestClient, settings: Settings) -> None:
    response = client.get("/api/session")
    assert response.status_code == 200
    assert response.json()["token"] == settings.token
    assert response.headers["cache-control"] == "no-store"


def test_config_requires_token(client: TestClient) -> None:
    assert client.get("/api/config").status_code == 401


def test_config_with_token(auth_client: TestClient, settings: Settings) -> None:
    response = auth_client.get("/api/config")
    assert response.status_code == 200
    payload = response.json()
    assert payload["default_destination"] == str(settings.allowed_roots[0])
    assert payload["roots"][0]["path"] == str(settings.allowed_roots[0])


def test_foreign_origin_is_rejected(auth_client: TestClient) -> None:
    response = auth_client.get(
        "/api/config",
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403


def test_cross_site_fetch_is_rejected(auth_client: TestClient) -> None:
    response = auth_client.get(
        "/api/config",
        headers={"Sec-Fetch-Site": "cross-site"},
    )
    assert response.status_code == 403


def test_foreign_host_is_rejected(client: TestClient) -> None:
    response = client.get("/api/health", headers={"Host": "evil.example"})
    assert response.status_code == 400


def test_analyze_rejects_file_urls(auth_client: TestClient) -> None:
    response = auth_client.post("/api/analyze", json={"url": "file:///etc/passwd"})
    assert response.status_code == 400
    assert "HTTP" in response.json()["detail"]["message"]


def test_analyze_rejects_private_networks(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/analyze", json={"url": "http://192.168.1.10/video"}
    )
    assert response.status_code == 400


def test_analyze_validates_body(auth_client: TestClient) -> None:
    response = auth_client.post("/api/analyze", json={"url": "x"})
    assert response.status_code == 422
    assert response.json()["detail"]["message"] == "La solicitud no es válida."


def test_fs_list_traversal_is_rejected(
    auth_client: TestClient, settings: Settings
) -> None:
    response = auth_client.get(
        "/api/fs/list",
        params={"path": str(settings.allowed_roots[0] / "..")},
    )
    assert response.status_code == 403


def test_fs_mkdir_and_list(auth_client: TestClient, settings: Settings) -> None:
    response = auth_client.post(
        "/api/fs/mkdir",
        json={"path": str(settings.allowed_roots[0]), "name": "Nueva"},
    )
    assert response.status_code == 201
    response = auth_client.get(
        "/api/fs/list", params={"path": str(settings.allowed_roots[0])}
    )
    assert response.status_code == 200
    assert any(item["name"] == "Nueva" for item in response.json()["directories"])


def test_unknown_download(auth_client: TestClient) -> None:
    assert auth_client.get("/api/downloads/missing").status_code == 404
    assert auth_client.post("/api/downloads/missing/cancel").status_code == 404


def test_websocket_rejects_wrong_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/ws/downloads/missing",
            subprotocols=["local-ytdlp", "wrong-token"],
        ):
            pass
    assert exc.value.code == 1008


def test_cors_preflight_for_dev_origin(client: TestClient) -> None:
    response = client.options(
        "/api/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-api-token,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_update_dependency_requires_token(client: TestClient) -> None:
    response = client.post("/api/dependencies/update", json={"tool": "ytdlp"})
    assert response.status_code == 401


def test_update_dependency_rejects_unknown_tool(auth_client: TestClient) -> None:
    response = auth_client.post("/api/dependencies/update", json={"tool": "curl"})
    assert response.status_code == 422


def test_update_dependency_returns_refreshed_state(
    auth_client: TestClient, monkeypatch
) -> None:
    ctx = auth_client.app.state.ctx

    async def fake_update(tool: str) -> ToolUpdateResult:
        assert tool == "ytdlp"
        return ToolUpdateResult(True)

    async def fake_dependencies(refresh: bool = False) -> dict:
        assert refresh is True
        return {
            "ok": True,
            "ytdlp": {
                "installed": True,
                "version": "2026.11.01",
                "path": "/tmp/yt-dlp",
            },
            "ffmpeg": {
                "installed": True,
                "version": "9.0.2",
                "path": "/usr/bin/ffmpeg",
            },
        }

    async def fake_check(**_kwargs) -> dict:
        return {
            "app": {
                "installed": "1.0.0",
                "latest": "1.0.0",
                "update_available": False,
                "error": None,
            },
            "ytdlp": {
                "installed": "2026.11.01",
                "latest": "2026.11.01",
                "update_available": False,
                "error": None,
            },
            "ffmpeg": {
                "installed": "9.0.2",
                "latest": "9.0.2",
                "update_available": False,
                "error": None,
            },
            "checked_at": "2026-11-09T12:00:00+00:00",
        }

    monkeypatch.setattr(ctx.tools, "update", fake_update)
    monkeypatch.setattr(ctx.tools, "dependencies", fake_dependencies)
    monkeypatch.setattr(ctx.updates, "check", fake_check)

    response = auth_client.post(
        "/api/dependencies/update", json={"tool": "ytdlp"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["updated"] is True
    assert payload["version"] == "2026.11.01"
    assert payload["dependencies"]["ytdlp"]["version"] == "2026.11.01"
    assert payload["check"]["ytdlp"]["update_available"] is False


def test_update_dependency_returns_failure_hint(
    auth_client: TestClient, monkeypatch
) -> None:
    ctx = auth_client.app.state.ctx

    async def fake_update(_tool: str) -> ToolUpdateResult:
        return ToolUpdateResult(
            False,
            error="ERROR: Permission denied",
            hint="La actualización necesita permisos de administrador.",
        )

    async def fake_dependencies(refresh: bool = False) -> dict:
        assert refresh is True
        return {
            "ok": True,
            "ytdlp": {
                "installed": True,
                "version": "2026.10.26",
                "path": "/tmp/yt-dlp",
            },
            "ffmpeg": {
                "installed": True,
                "version": "9.0.2",
                "path": "/usr/bin/ffmpeg",
            },
        }

    async def fail_check(**_kwargs) -> dict:  # pragma: no cover - must not run
        raise AssertionError("check should not run after a failed update")

    monkeypatch.setattr(ctx.tools, "update", fake_update)
    monkeypatch.setattr(ctx.tools, "dependencies", fake_dependencies)
    monkeypatch.setattr(ctx.updates, "check", fail_check)

    response = auth_client.post(
        "/api/dependencies/update", json={"tool": "ytdlp"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["updated"] is False
    assert payload["error"] == "ERROR: Permission denied"
    assert "permisos" in payload["hint"]
    assert payload["check"] is None
