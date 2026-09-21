from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libraries.database.models import Base
from libraries.database.session import get_session
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

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_health_check(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    async def test_readiness_check(self, client: AsyncClient) -> None:
        response = await client.get("/ready")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
class TestEventEndpoints:
    async def test_create_event(self, client: AsyncClient) -> None:
        response = await client.post(
            "/events",
            json={
                "event_type": "LOGIN_FAILED",
                "source": "auth_service",
                "producer": "auth_v1",
                "payload": {"user_id": "u123"},
                "severity": "info",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"
        assert data["event_id"].startswith("evt_")

    async def test_create_event_minimal(self, client: AsyncClient) -> None:
        response = await client.post(
            "/events",
            json={
                "event_type": "TEST",
                "source": "test",
                "producer": "test",
            },
        )
        assert response.status_code == 201

    async def test_create_event_missing_fields(self, client: AsyncClient) -> None:
        response = await client.post(
            "/events",
            json={"event_type": "TEST"},
        )
        assert response.status_code == 422

    async def test_create_event_empty_source(self, client: AsyncClient) -> None:
        response = await client.post(
            "/events",
            json={
                "event_type": "TEST",
                "source": "",
                "producer": "test",
            },
        )
        assert response.status_code == 422

    async def test_duplicate_event_returns_409(self, client: AsyncClient) -> None:
        event_data = {
            "event_type": "TEST",
            "source": "test",
            "producer": "test",
        }
        response1 = await client.post("/events", json=event_data)
        assert response1.status_code == 201
        response1.json()["event_id"]

        response2 = await client.post(
            "/events",
            json={
                "event_type": "TEST",
                "source": "test",
                "producer": "test",
            },
        )
        assert response2.status_code == 201

    async def test_create_event_with_all_fields(self, client: AsyncClient) -> None:
        response = await client.post(
            "/events",
            json={
                "event_type": "AGENT_STEP",
                "source": "agent_runtime",
                "producer": "agent_v1",
                "payload": {"step": 1, "tool": "search"},
                "metadata": {"version": "1.0"},
                "severity": "info",
                "tenant_id": "tenant_1",
                "trace_id": "trace_abc",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["event_id"].startswith("evt_")
