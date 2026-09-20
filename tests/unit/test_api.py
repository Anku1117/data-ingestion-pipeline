from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.ingestion.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestHealthEndpoints:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    def test_readiness_check(self, client: TestClient) -> None:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


class TestEventEndpoints:
    def test_create_event(self, client: TestClient) -> None:
        response = client.post(
            "/events",
            json={
                "event_type": "LOGIN_FAILED",
                "source": "auth_service",
                "producer": "auth_v1",
                "payload": {"user_id": "u123"},
                "severity": "info",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["event_id"].startswith("evt_")

    def test_create_event_minimal(self, client: TestClient) -> None:
        response = client.post(
            "/events",
            json={
                "event_type": "TEST",
                "source": "test",
                "producer": "test",
            },
        )
        assert response.status_code == 202

    def test_create_event_missing_fields(self, client: TestClient) -> None:
        response = client.post(
            "/events",
            json={"event_type": "TEST"},
        )
        assert response.status_code == 422

    def test_create_event_empty_source(self, client: TestClient) -> None:
        response = client.post(
            "/events",
            json={
                "event_type": "TEST",
                "source": "",
                "producer": "test",
            },
        )
        assert response.status_code == 422
