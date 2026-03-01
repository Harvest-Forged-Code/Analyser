from __future__ import annotations

from unittest.mock import patch

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


def test_version_endpoint_delegates_to_get_version() -> None:
    with patch("budget_analyser.api.main.get_version", return_value="9.8.7"):
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get("/api/version")
    assert response.status_code == 200
    assert response.json() == {"version": "9.8.7"}
