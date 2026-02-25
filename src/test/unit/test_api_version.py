from __future__ import annotations

from fastapi.testclient import TestClient

from budget_analyser.api.main import create_app


def test_version_endpoint_returns_version_string() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0
