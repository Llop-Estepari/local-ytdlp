from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import Settings


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
