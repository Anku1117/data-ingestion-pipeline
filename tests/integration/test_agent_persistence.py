from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libraries.database.agent_models import (
    AgentEvaluationRecord,
    AgentRunRecord,
    AgentStepRecord,
    AgentTaskRecord,
)
from libraries.database.models import Base
from libraries.database.repositories import (
    SQLAlchemyAgentEvaluationRepository,
    SQLAlchemyAgentRunRepository,
    SQLAlchemyAgentStepRepository,
    SQLAlchemyAgentTaskRepository,
)
from libraries.database.session import get_session
from services.agent_data.models import (
    AgentEvaluation,
    AgentRun,
    AgentStep,
    AgentTask,
    RunStatus,
    StepType,
)
from services.agent_data.service import AgentDataService
from services.ingestion.main import create_app


@pytest.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(async_engine):
    return async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def service(session_factory):
    async with session_factory() as session:
        run_repo = SQLAlchemyAgentRunRepository(session)
        step_repo = SQLAlchemyAgentStepRepository(session)
        eval_repo = SQLAlchemyAgentEvaluationRepository(session)
        task_repo = SQLAlchemyAgentTaskRepository(session)
        svc = AgentDataService(
            run_repo=run_repo,
            step_repo=step_repo,
            evaluation_repo=eval_repo,
            task_repo=task_repo,
        )
        yield svc
        await session.rollback()


@pytest.fixture
async def client(async_engine):
    from libraries.security.auth import verify_api_key
    from libraries.security.rate_limit import rate_limit

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
class TestAgentPersistence:
    async def test_create_task_persists(self, service: AgentDataService) -> None:
        task = AgentTask(description="Test task", agent_id="agent_1")
        await service.create_task(task)
        assert task.task_id.startswith("task_")

    async def test_start_run_persists(self, service: AgentDataService) -> None:
        task = AgentTask(description="Test", agent_id="agent_1")
        await service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_1")
        await service.start_run(run)
        assert run.run_id.startswith("run_")
        assert run.status == RunStatus.PENDING

    async def test_complete_run_persists(self, service: AgentDataService) -> None:
        task = AgentTask(description="Test", agent_id="agent_1")
        await service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_1")
        await service.start_run(run)

        completed = await service.complete_run(run.run_id, outcome="success")
        assert completed is not None
        assert completed.status == RunStatus.COMPLETED
        assert completed.outcome == "success"
        assert completed.ended_at is not None

    async def test_fail_run_persists(self, service: AgentDataService) -> None:
        task = AgentTask(description="Test", agent_id="agent_1")
        await service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_1")
        await service.start_run(run)

        failed = await service.fail_run(run.run_id, error="timeout")
        assert failed is not None
        assert failed.status == RunStatus.FAILED
        assert failed.outcome == "timeout"

    async def test_record_step_persists(self, service: AgentDataService) -> None:
        task = AgentTask(description="Test", agent_id="agent_1")
        await service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_1")
        await service.start_run(run)

        step = AgentStep(
            run_id=run.run_id,
            step_number=1,
            step_type=StepType.MODEL_CALL,
            input_tokens=100,
            output_tokens=50,
            latency_ms=250.0,
        )
        await service.record_step(step)
        assert step.step_id.startswith("step_")

    async def test_trajectory_reconstruction(self, service: AgentDataService) -> None:
        task = AgentTask(description="Test", agent_id="agent_1")
        await service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_1")
        await service.start_run(run)

        step1 = AgentStep(
            run_id=run.run_id,
            step_number=1,
            step_type=StepType.MODEL_CALL,
            input_tokens=100,
            output_tokens=50,
            latency_ms=200.0,
        )
        step2 = AgentStep(
            run_id=run.run_id,
            step_number=2,
            step_type=StepType.TOOL_CALL,
            tool_name="search",
            input_tokens=20,
            output_tokens=100,
            latency_ms=150.0,
        )
        await service.record_step(step1)
        await service.record_step(step2)

        trajectory = await service.get_trajectory(run.run_id)
        assert trajectory is not None
        assert len(trajectory.steps) == 2
        assert trajectory.total_latency_ms == 350.0
        assert trajectory.total_tokens == 270

    async def test_evaluation_persists(self, service: AgentDataService) -> None:
        task = AgentTask(description="Test", agent_id="agent_1")
        await service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_1")
        await service.start_run(run)

        evaluation = AgentEvaluation(
            run_id=run.run_id,
            agent_id="agent_1",
            success=True,
            score=0.92,
            total_tokens=300,
        )
        await service.create_evaluation(evaluation)

        retrieved = await service.get_evaluation_by_run_id(run.run_id)
        assert retrieved is not None
        assert retrieved.score == 0.92
        assert retrieved.success is True

    async def test_duplicate_step_persists(self, service: AgentDataService) -> None:
        task = AgentTask(description="Test", agent_id="agent_1")
        await service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_1")
        await service.start_run(run)

        step = AgentStep(
            run_id=run.run_id,
            step_number=1,
            step_type=StepType.MODEL_CALL,
        )
        await service.record_step(step)

        step2 = AgentStep(
            run_id=run.run_id,
            step_number=1,
            step_type=StepType.MODEL_CALL,
        )
        await service.record_step(step2)

        steps = await service._step_repo.list_by_run(run.run_id)
        assert len(steps) == 2

    async def test_missing_run_returns_none(self, service: AgentDataService) -> None:
        result = await service.get_run("nonexistent_run_id")
        assert result is None

    async def test_missing_trajectory_returns_none(self, service: AgentDataService) -> None:
        result = await service.get_trajectory("nonexistent_run_id")
        assert result is None


@pytest.mark.asyncio
class TestAgentAPIPersistence:
    async def test_create_task_via_api(self, client: AsyncClient) -> None:
        response = await client.post(
            "/agents/tasks",
            json={"agent_id": "agent_1", "description": "API task"},
        )
        assert response.status_code in (200, 201, 404)

    async def test_list_runs_empty(self, client: AsyncClient) -> None:
        response = await client.get("/agents/runs")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "runs" in data

    async def test_get_run_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/agents/runs/nonexistent")
        assert response.status_code == 404

    async def test_list_evaluations_empty(self, client: AsyncClient) -> None:
        response = await client.get("/agents/evaluations")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "evaluations" in data

    async def test_get_trajectory_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/agents/runs/nonexistent/trajectory")
        assert response.status_code == 404
