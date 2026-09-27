from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libraries.database.models import Base
from libraries.database.session import get_session
from libraries.security.auth import verify_api_key
from libraries.security.rate_limit import rate_limit


@pytest.fixture(autouse=True)
def _reset_global_state():
    import libraries.cache.factory as cache_factory
    import libraries.security.rate_limit as rl

    rl._default_limiter = None
    cache_factory._cache = None
    yield
    rl._default_limiter = None
    cache_factory._cache = None


async def _noop_rate_limit() -> None:
    pass


async def _noop_api_key() -> str | None:
    return None


@pytest.fixture
def app_with_overrides():
    from services.ingestion.main import create_app

    app = create_app()
    app.dependency_overrides[rate_limit] = _noop_rate_limit
    app.dependency_overrides[verify_api_key] = _noop_api_key
    return app


@pytest.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session
