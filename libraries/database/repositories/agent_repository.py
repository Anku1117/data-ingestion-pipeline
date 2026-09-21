from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from libraries.database.agent_models import (
    AgentEvaluationRecord,
    AgentRunRecord,
    AgentStepRecord,
    AgentTaskRecord,
)
from libraries.database.repositories.agent_base import (
    AgentEvaluationRepository,
    AgentRunRepository,
    AgentStepRepository,
    AgentTaskRepository,
)
from libraries.logging.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from services.agent_data.models import AgentEvaluation, AgentRun, AgentStep, AgentTask

logger = get_logger(__name__)


class SQLAlchemyAgentRunRepository(AgentRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_record(self, run: AgentRun) -> AgentRunRecord:
        return AgentRunRecord(
            run_id=run.run_id,
            task_id=run.task_id,
            agent_id=run.agent_id,
            session_id=run.session_id,
            status=run.status.value,
            started_at=run.started_at,
            ended_at=run.ended_at,
            outcome=run.outcome,
            total_tokens=run.total_tokens,
            total_steps=run.total_steps,
            metadata_=run.metadata,
        )

    def _to_model(self, record: AgentRunRecord) -> AgentRun:
        from services.agent_data.models import AgentRun, RunStatus

        return AgentRun(
            run_id=record.run_id,
            task_id=record.task_id,
            agent_id=record.agent_id,
            session_id=record.session_id,
            status=RunStatus(record.status),
            started_at=record.started_at,
            ended_at=record.ended_at,
            outcome=record.outcome,
            total_tokens=record.total_tokens,
            total_steps=record.total_steps,
            metadata=record.metadata_,
        )

    async def create(self, run: AgentRun) -> None:
        record = self._to_record(run)
        self._session.add(record)
        await self._session.flush()
        logger.info("Agent run persisted run_id=%s", run.run_id)

    async def get_by_id(self, run_id: str) -> AgentRun | None:
        stmt = select(AgentRunRecord).where(AgentRunRecord.run_id == run_id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_model(record) if record else None

    async def update(self, run: AgentRun) -> None:
        stmt = select(AgentRunRecord).where(AgentRunRecord.run_id == run.run_id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return
        record.status = run.status.value
        record.ended_at = run.ended_at
        record.outcome = run.outcome
        record.total_tokens = run.total_tokens
        record.total_steps = run.total_steps
        record.metadata_ = run.metadata
        await self._session.flush()

    async def list_runs(
        self,
        agent_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        stmt = select(AgentRunRecord)
        count_stmt = select(func.count()).select_from(AgentRunRecord)

        if agent_id:
            stmt = stmt.where(AgentRunRecord.agent_id == agent_id)
            count_stmt = count_stmt.where(AgentRunRecord.agent_id == agent_id)
        if status:
            stmt = stmt.where(AgentRunRecord.status == status)
            count_stmt = count_stmt.where(AgentRunRecord.status == status)

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(AgentRunRecord.started_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        records = result.scalars().all()

        return {
            "total": total,
            "runs": [self._to_model(r).model_dump(mode="json") for r in records],
            "limit": limit,
            "offset": offset,
        }

    async def count_steps(self, run_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(AgentStepRecord)
            .where(AgentStepRecord.run_id == run_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0


class SQLAlchemyAgentStepRepository(AgentStepRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_record(self, step: AgentStep) -> AgentStepRecord:
        return AgentStepRecord(
            step_id=step.step_id,
            run_id=step.run_id,
            step_number=step.step_number,
            step_type=step.step_type.value,
            timestamp=step.timestamp,
            trace_id=step.trace_id,
            parent_event_id=step.parent_event_id,
            model_id=step.model_id,
            model_name=step.model_name,
            input_tokens=step.input_tokens,
            output_tokens=step.output_tokens,
            latency_ms=step.latency_ms,
            tool_name=step.tool_name,
            tool_status=step.tool_status,
            tool_input=step.tool_input,
            tool_output=step.tool_output,
            retrieval_ids=step.retrieval_ids,
            error=step.error,
            metadata_=step.metadata,
        )

    def _to_model(self, record: AgentStepRecord) -> AgentStep:
        from services.agent_data.models import AgentStep, StepType

        return AgentStep(
            step_id=record.step_id,
            run_id=record.run_id,
            step_number=record.step_number,
            step_type=StepType(record.step_type),
            timestamp=record.timestamp,
            trace_id=record.trace_id,
            parent_event_id=record.parent_event_id,
            model_id=record.model_id,
            model_name=record.model_name,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            latency_ms=record.latency_ms,
            tool_name=record.tool_name,
            tool_status=record.tool_status,
            tool_input=record.tool_input,
            tool_output=record.tool_output,
            retrieval_ids=record.retrieval_ids or [],
            error=record.error,
            metadata=record.metadata_,
        )

    async def create(self, step: AgentStep) -> None:
        record = self._to_record(step)
        self._session.add(record)
        await self._session.flush()

    async def list_by_run(self, run_id: str) -> list[AgentStep]:
        stmt = (
            select(AgentStepRecord)
            .where(AgentStepRecord.run_id == run_id)
            .order_by(AgentStepRecord.step_number)
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._to_model(r) for r in records]

    async def count_by_run(self, run_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(AgentStepRecord)
            .where(AgentStepRecord.run_id == run_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0


class SQLAlchemyAgentEvaluationRepository(AgentEvaluationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_record(self, evaluation: AgentEvaluation) -> AgentEvaluationRecord:
        return AgentEvaluationRecord(
            evaluation_id=evaluation.evaluation_id,
            run_id=evaluation.run_id,
            agent_id=evaluation.agent_id,
            success=evaluation.success,
            score=evaluation.score,
            latency_ms=evaluation.latency_ms,
            total_tokens=evaluation.total_tokens,
            tool_failures=evaluation.tool_failures,
            task_completion=evaluation.task_completion,
            anomaly_score=evaluation.anomaly_score,
            metadata_=evaluation.metadata,
            created_at=evaluation.created_at,
        )

    def _to_model(self, record: AgentEvaluationRecord) -> AgentEvaluation:
        from services.agent_data.models import AgentEvaluation

        return AgentEvaluation(
            evaluation_id=record.evaluation_id,
            run_id=record.run_id,
            agent_id=record.agent_id,
            success=record.success,
            score=record.score,
            latency_ms=record.latency_ms,
            total_tokens=record.total_tokens,
            tool_failures=record.tool_failures,
            task_completion=record.task_completion,
            anomaly_score=record.anomaly_score,
            metadata=record.metadata_,
            created_at=record.created_at,
        )

    async def create(self, evaluation: AgentEvaluation) -> None:
        record = self._to_record(evaluation)
        self._session.add(record)
        await self._session.flush()
        logger.info("Agent evaluation persisted run_id=%s", evaluation.run_id)

    async def get_by_run_id(self, run_id: str) -> AgentEvaluation | None:
        stmt = select(AgentEvaluationRecord).where(AgentEvaluationRecord.run_id == run_id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_model(record) if record else None

    async def list_evaluations(
        self,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        stmt = select(AgentEvaluationRecord)
        count_stmt = select(func.count()).select_from(AgentEvaluationRecord)

        if agent_id:
            stmt = stmt.where(AgentEvaluationRecord.agent_id == agent_id)
            count_stmt = count_stmt.where(AgentEvaluationRecord.agent_id == agent_id)

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(AgentEvaluationRecord.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        records = result.scalars().all()

        return {
            "total": total,
            "evaluations": [self._to_model(r).model_dump(mode="json") for r in records],
            "limit": limit,
            "offset": offset,
        }


class SQLAlchemyAgentTaskRepository(AgentTaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_record(self, task: AgentTask) -> AgentTaskRecord:
        return AgentTaskRecord(
            task_id=task.task_id,
            agent_id=task.agent_id,
            description=task.description,
            metadata_=task.metadata,
            created_at=task.created_at,
        )

    def _to_model(self, record: AgentTaskRecord) -> AgentTask:
        from services.agent_data.models import AgentTask

        return AgentTask(
            task_id=record.task_id,
            agent_id=record.agent_id,
            description=record.description,
            metadata=record.metadata_,
            created_at=record.created_at,
        )

    async def create(self, task: AgentTask) -> None:
        record = self._to_record(task)
        self._session.add(record)
        await self._session.flush()

    async def get_by_id(self, task_id: str) -> AgentTask | None:
        stmt = select(AgentTaskRecord).where(AgentTaskRecord.task_id == task_id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_model(record) if record else None
