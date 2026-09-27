from __future__ import annotations

from typing import Any

from libraries.event_backend import get_event_backend
from libraries.logging.logging import get_logger
from libraries.observability.metrics import timed
from libraries.schemas.common import EventEnvelope
from services.agent_data.models import (
    AgentEvaluation,
    AgentRun,
    AgentStep,
    AgentTask,
    AgentTrajectory,
    RunStatus,
)

logger = get_logger(__name__)


class AgentDataService:
    """Service for agent telemetry, trajectories, and evaluation.

    Uses repositories for persistent storage. Falls back to in-memory
    when no repositories are provided (for backward compatibility).
    """

    def __init__(
        self,
        run_repo: Any = None,
        step_repo: Any = None,
        evaluation_repo: Any = None,
        task_repo: Any = None,
    ) -> None:
        self._run_repo = run_repo
        self._step_repo = step_repo
        self._evaluation_repo = evaluation_repo
        self._task_repo = task_repo

        self._use_persistence = run_repo is not None

        if not self._use_persistence:
            self._runs: dict[str, AgentRun] = {}
            self._steps: dict[str, list[AgentStep]] = {}
            self._tasks: dict[str, AgentTask] = {}
            self._evaluations: dict[str, AgentEvaluation] = {}

        logger.info("AgentDataService initialized persistence=%s", self._use_persistence)

    @timed("agent.create_task")
    async def create_task(self, task: AgentTask) -> AgentTask:
        if self._use_persistence:
            await self._task_repo.create(task)
        else:
            self._tasks[task.task_id] = task

        await self._publish_agent_event(
            "AGENT_TASK_CREATED", task.task_id, task.model_dump(mode="json")
        )
        logger.info("Task created task_id=%s agent_id=%s", task.task_id, task.agent_id)
        return task

    @timed("agent.start_run")
    async def start_run(self, run: AgentRun) -> AgentRun:
        if self._use_persistence:
            await self._run_repo.create(run)
        else:
            self._runs[run.run_id] = run
            self._steps[run.run_id] = []

        await self._publish_agent_event(
            "AGENT_RUN_STARTED", run.run_id, run.model_dump(mode="json")
        )
        logger.info("Run started run_id=%s agent_id=%s", run.run_id, run.agent_id)
        return run

    @timed("agent.complete_run")
    async def complete_run(self, run_id: str, outcome: str | None = None) -> AgentRun | None:
        if self._use_persistence:
            run = await self._run_repo.get_by_id(run_id)
        else:
            run = self._runs.get(run_id)

        if run is None:
            return None

        from datetime import UTC, datetime

        run.status = RunStatus.COMPLETED
        run.ended_at = datetime.now(UTC)
        run.outcome = outcome

        if self._use_persistence:
            run.total_steps = await self._step_repo.count_by_run(run_id)
            await self._run_repo.update(run)
        else:
            run.total_steps = len(self._steps.get(run_id, []))

        await self._publish_agent_event("AGENT_RUN_COMPLETED", run_id, run.model_dump(mode="json"))
        logger.info("Run completed run_id=%s outcome=%s", run_id, outcome)
        return run

    @timed("agent.fail_run")
    async def fail_run(self, run_id: str, error: str | None = None) -> AgentRun | None:
        if self._use_persistence:
            run = await self._run_repo.get_by_id(run_id)
        else:
            run = self._runs.get(run_id)

        if run is None:
            return None

        from datetime import UTC, datetime

        run.status = RunStatus.FAILED
        run.ended_at = datetime.now(UTC)
        run.outcome = error

        if self._use_persistence:
            await self._run_repo.update(run)
        await self._publish_agent_event("AGENT_RUN_FAILED", run_id, run.model_dump(mode="json"))
        logger.info("Run failed run_id=%s error=%s", run_id, error)
        return run

    @timed("agent.record_step")
    async def record_step(self, step: AgentStep) -> AgentStep:
        if self._use_persistence:
            await self._step_repo.create(step)
        else:
            if step.run_id not in self._steps:
                self._steps[step.run_id] = []
            self._steps[step.run_id].append(step)

        await self._publish_agent_event(
            f"AGENT_{step.step_type.value.upper()}",
            step.run_id,
            step.model_dump(mode="json"),
        )
        logger.debug("Step recorded run_id=%s step_type=%s", step.run_id, step.step_type)
        return step

    @timed("agent.get_trajectory")
    async def get_trajectory(self, run_id: str) -> AgentTrajectory | None:
        if self._use_persistence:
            run = await self._run_repo.get_by_id(run_id)
        else:
            run = self._runs.get(run_id)

        if run is None:
            return None

        if self._use_persistence:
            steps = await self._step_repo.list_by_run(run_id)
        else:
            steps = self._steps.get(run_id, [])

        total_latency = sum(s.latency_ms for s in steps)
        total_tokens = sum(s.input_tokens + s.output_tokens for s in steps)

        return AgentTrajectory(
            run_id=run_id,
            agent_id=run.agent_id,
            task_id=run.task_id,
            steps=steps,
            outcome=run.outcome,
            total_tokens=total_tokens,
            total_latency_ms=total_latency,
        )

    async def create_evaluation(self, evaluation: AgentEvaluation) -> AgentEvaluation:
        if self._use_persistence:
            await self._evaluation_repo.create(evaluation)
        else:
            self._evaluations[evaluation.run_id] = evaluation

        await self._publish_agent_event(
            "AGENT_EVALUATION", evaluation.run_id, evaluation.model_dump(mode="json")
        )
        logger.info(
            "Evaluation created run_id=%s score=%.2f success=%s",
            evaluation.run_id,
            evaluation.score,
            evaluation.success,
        )
        return evaluation

    async def get_runs(
        self,
        agent_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        if self._use_persistence:
            return await self._run_repo.list_runs(agent_id, status, limit, offset)

        runs = list(self._runs.values())
        if agent_id:
            runs = [r for r in runs if r.agent_id == agent_id]
        if status:
            runs = [r for r in runs if r.status.value == status]
        runs.sort(key=lambda r: r.started_at, reverse=True)
        total = len(runs)
        page = runs[offset : offset + limit]
        return {
            "total": total,
            "runs": [r.model_dump(mode="json") for r in page],
            "limit": limit,
            "offset": offset,
        }

    async def get_run(self, run_id: str) -> AgentRun | None:
        if self._use_persistence:
            return await self._run_repo.get_by_id(run_id)
        return self._runs.get(run_id)

    async def get_evaluations(
        self,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        if self._use_persistence:
            return await self._evaluation_repo.list_evaluations(agent_id, limit, offset)

        evals = list(self._evaluations.values())
        if agent_id:
            evals = [e for e in evals if e.agent_id == agent_id]
        evals.sort(key=lambda e: e.created_at, reverse=True)
        total = len(evals)
        page = evals[offset : offset + limit]
        return {
            "total": total,
            "evaluations": [e.model_dump(mode="json") for e in page],
            "limit": limit,
            "offset": offset,
        }

    async def get_evaluation_by_run_id(self, run_id: str) -> AgentEvaluation | None:
        if self._use_persistence:
            return await self._evaluation_repo.get_by_run_id(run_id)
        return self._evaluations.get(run_id)

    async def export_training_dataset(
        self,
        run_ids: list[str] | None = None,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        entries = []

        if self._use_persistence:
            if run_ids:
                target_runs = []
                for rid in run_ids:
                    run = await self._run_repo.get_by_id(rid)
                    if run:
                        target_runs.append(run)
            else:
                result = await self._run_repo.list_runs(limit=10000)
                target_runs = [AgentRun(**r) for r in result.get("runs", [])]
        else:
            target_runs = (
                list(self._runs.values())
                if run_ids is None
                else [self._runs[rid] for rid in run_ids if rid in self._runs]
            )

        for run in target_runs:
            trajectory = await self.get_trajectory(run.run_id)
            if trajectory is None:
                continue

            evaluation = await self._get_evaluation_for_export(run.run_id)
            if evaluation and min_score is not None and evaluation.score < min_score:
                continue

            entry = {
                "run_id": run.run_id,
                "task_id": run.task_id,
                "agent_id": run.agent_id,
                "trajectory": trajectory.model_dump(mode="json"),
                "outcome": run.outcome,
                "evaluation": evaluation.model_dump(mode="json") if evaluation else None,
                "metadata": {
                    "total_tokens": run.total_tokens,
                    "total_steps": run.total_steps,
                    "status": run.status.value,
                },
            }
            entries.append(entry)

        return entries

    async def _get_evaluation_for_export(self, run_id: str) -> AgentEvaluation | None:
        if self._use_persistence:
            return await self._evaluation_repo.get_by_run_id(run_id)
        return self._evaluations.get(run_id)

    async def _publish_agent_event(
        self, event_type: str, run_id: str, data: dict[str, Any]
    ) -> None:
        try:
            backend = get_event_backend()
            event = EventEnvelope(
                event_type=event_type,
                source="agent_runtime",
                producer="agent_data_service",
                run_id=run_id,
                payload=data,
            )
            await backend.publish("dip-agent", event)
        except Exception as e:
            logger.error("Failed to publish agent event: %s", str(e))
