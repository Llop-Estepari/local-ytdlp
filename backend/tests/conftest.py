from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings.for_testing(tmp_path)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(client: TestClient, settings: Settings) -> TestClient:
    client.headers.update({"X-API-Token": settings.token})
    return client
