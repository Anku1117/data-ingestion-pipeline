from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libraries.database.models import Base
from libraries.database.session import get_session
from libraries.security.auth import verify_api_key
from libraries.security.rate_limit import rate_limit
from services.ingestion.main import create_app


@pytest.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(async_engine):
    factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_session():
        async with factory() as session:
            yield session

    async def _noop_rate_limit() -> None:
        pass

    async def _noop_api_key() -> str | None:
        return None

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[rate_limit] = _noop_rate_limit
    app.dependency_overrides[verify_api_key] = _noop_api_key
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestE2EEventFlow:
    """End-to-end: Event ingestion -> persistence -> retrieval."""

    async def test_full_event_lifecycle(self, client: AsyncClient) -> None:
        response = await client.post(
            "/events",
            json={
                "event_type": "LOGIN_FAILED",
                "source": "auth_service",
                "producer": "auth_v1",
                "payload": {"user_id": "u123", "ip_address": "10.0.0.1"},
                "severity": "warning",
            },
        )
        assert response.status_code == 201
        data = response.json()
        event_id = data["event_id"]
        assert event_id.startswith("evt_")
        assert data["status"] == "created"

        response = await client.get(f"/events/{event_id}")
        assert response.status_code == 200
        event = response.json()
        assert event["event_type"] == "LOGIN_FAILED"
        assert event["source"] == "auth_service"

    async def test_events_list_with_filter(self, client: AsyncClient) -> None:
        await client.post(
            "/events",
            json={"event_type": "TEST_A", "source": "src1", "producer": "p1"},
        )
        await client.post(
            "/events",
            json={"event_type": "TEST_B", "source": "src2", "producer": "p2"},
        )

        response = await client.get("/events?event_type=TEST_A")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_health_ready_flow(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        resp = await client.get("/ready")
        assert resp.status_code == 200

    async def test_pipeline_status(self, client: AsyncClient) -> None:
        resp = await client.get("/pipeline/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "event_backend" in data
        assert "search_backend" in data
        assert "metrics" in data

    async def test_pipeline_stats(self, client: AsyncClient) -> None:
        resp = await client.get("/pipeline/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "pipeline" in data
        assert "detector" in data

    async def test_threats_endpoint(self, client: AsyncClient) -> None:
        resp = await client.get("/threats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "alerts" in data

    async def test_threat_rules(self, client: AsyncClient) -> None:
        resp = await client.get("/threats/rules")
        assert resp.status_code == 200
        rules = resp.json()
        assert len(rules) > 0
        assert all("name" in r and "description" in r for r in rules)

    async def test_agent_runs_endpoint(self, client: AsyncClient) -> None:
        resp = await client.get("/agents/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "runs" in data

    async def test_metrics_endpoint(self, client: AsyncClient) -> None:
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "counters" in data
        assert "timers" in data

    async def test_prometheus_endpoint(self, client: AsyncClient) -> None:
        resp = await client.get("/prometheus")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
