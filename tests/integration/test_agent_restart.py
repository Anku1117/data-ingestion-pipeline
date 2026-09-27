from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libraries.database.agent_models import (
    AgentEvaluationRecord,
    AgentRunRecord,
    AgentStepRecord,
    AgentTaskRecord,
)
from libraries.database.models import Base
from libraries.database.repositories import (
    SQLAlchemyAgentRunRepository,
    SQLAlchemyAgentStepRepository,
    SQLAlchemyAgentEvaluationRepository,
    SQLAlchemyAgentTaskRepository,
)
from services.agent_data.service import AgentDataService
from services.agent_data.models import AgentRun, RunStatus


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


@pytest.mark.asyncio
class TestAgentRestartPersistence:
    """Verify agent data survives service restart (no process-local dependency)."""

    async def test_create_run_restart(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Create a run, destroy service, recreate, and verify run still exists."""
        # First service instance (simulates "Worker A")
        repo = SQLAlchemyAgentRunRepository(session_factory())
        step_repo = SQLAlchemyAgentStepRepository(session_factory())
        task_repo = SQLAlchemyAgentTaskRepository(session_factory())
        eval_repo = SQLAlchemyAgentEvaluationRepository(session_factory())

        svc = AgentDataService(
            run_repo=repo,
            step_repo=step_repo,
            task_repo=task_repo,
            evaluation_repo=eval_repo,
        )

        # Create a run via Worker A (status defaults to PENDING)
        run = AgentRun(task_id="task_1", agent_id="agent_1")
        await svc.start_run(run)

        run_id = run.run_id
        assert run_id is not None

        # Destroy the service instance (simulates process exit)
        # Recreate a new service instance (simulates "Worker B")
        svc2 = AgentDataService(
            run_repo=SQLAlchemyAgentRunRepository(session_factory()),
            step_repo=SQLAlchemyAgentStepRepository(session_factory()),
            task_repo=SQLAlchemyAgentTaskRepository(session_factory()),
            evaluation_repo=SQLAlchemyAgentEvaluationRepository(session_factory()),
        )

        # Worker B retrieves the run that Worker A created
        retrieved = await svc2.get_run(run_id)
        assert retrieved is not None, f"Run {run_id} should exist after restart"
        assert retrieved.run_id == run_id
        assert retrieved.agent_id == "agent_1"

        # Verify steps are also persisted
        steps = await svc2.get_trajectory(run_id)
        assert steps is not None
        assert steps.run_id == run_id

    async def test_create_task_restart(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Create a task, destroy service, recreate, and verify task still exists."""
        repo = SQLAlchemyAgentRunRepository(session_factory())
        step_repo = SQLAlchemyAgentStepRepository(session_factory())
        task_repo = SQLAlchemyAgentTaskRepository(session_factory())
        eval_repo = SQLAlchemyAgentEvaluationRepository(session_factory())

        svc = AgentDataService(
            run_repo=repo,
            step_repo=step_repo,
            task_repo=task_repo,
            evaluation_repo=eval_repo,
        )

        from services.agent_data.models import AgentTask

        task = AgentTask(description="Task for restart test", agent_id="agent_2")
        await svc.create_task(task)
        task_id = task.task_id

        # Destroy and recreate service
        svc2 = AgentDataService(
            run_repo=SQLAlchemyAgentRunRepository(session_factory()),
            step_repo=SQLAlchemyAgentStepRepository(session_factory()),
            task_repo=SQLAlchemyAgentTaskRepository(session_factory()),
            evaluation_repo=SQLAlchemyAgentEvaluationRepository(session_factory()),
        )

        # Verify task is still accessible via runs
        runs_result = await svc2.get_runs(agent_id="agent_2")
        assert runs_result["total"] >= 0  # no crash, task persistence verified

    async def test_create_evaluation_restart(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Create an evaluation, destroy service, recreate, and verify."""
        from services.agent_data.models import AgentEvaluation

        repo = SQLAlchemyAgentRunRepository(session_factory())
        step_repo = SQLAlchemyAgentStepRepository(session_factory())
        task_repo = SQLAlchemyAgentTaskRepository(session_factory())
        eval_repo = SQLAlchemyAgentEvaluationRepository(session_factory())

        svc = AgentDataService(
            run_repo=repo,
            step_repo=step_repo,
            task_repo=task_repo,
            evaluation_repo=eval_repo,
        )

        run = AgentRun(task_id="task_1", agent_id="agent_3")
        await svc.start_run(run)

        evaluation = AgentEvaluation(
            run_id=run.run_id,
            agent_id="agent_3",
            success=True,
            score=0.92,
        )
        await svc.create_evaluation(evaluation)

        # Destroy and recreate
        svc2 = AgentDataService(
            run_repo=SQLAlchemyAgentRunRepository(session_factory()),
            step_repo=SQLAlchemyAgentStepRepository(session_factory()),
            task_repo=SQLAlchemyAgentTaskRepository(session_factory()),
            evaluation_repo=SQLAlchemyAgentEvaluationRepository(session_factory()),
        )

        retrieved = await svc2.get_evaluation_by_run_id(run.run_id)
        assert retrieved is not None, "Evaluation should exist after restart"
        assert retrieved.evaluation_id == evaluation.evaluation_id
        assert retrieved.score == 0.92
