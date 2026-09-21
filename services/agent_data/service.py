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
    """Service for agent telemetry, trajectories, and evaluation."""

    def __init__(self) -> None:
        self._runs: dict[str, AgentRun] = {}
        self._steps: dict[str, list[AgentStep]] = {}
        self._tasks: dict[str, AgentTask] = {}
        self._evaluations: dict[str, AgentEvaluation] = {}
        logger.info("AgentDataService initialized")

    @timed("agent.create_task")
    async def create_task(self, task: AgentTask) -> AgentTask:
        self._tasks[task.task_id] = task
        await self._publish_agent_event(
            "AGENT_TASK_CREATED", task.task_id, task.model_dump(mode="json")
        )
        logger.info("Task created task_id=%s agent_id=%s", task.task_id, task.agent_id)
        return task

    @timed("agent.start_run")
    async def start_run(self, run: AgentRun) -> AgentRun:
        self._runs[run.run_id] = run
        self._steps[run.run_id] = []
        await self._publish_agent_event(
            "AGENT_RUN_STARTED", run.run_id, run.model_dump(mode="json")
        )
        logger.info("Run started run_id=%s agent_id=%s", run.run_id, run.agent_id)
        return run

    @timed("agent.complete_run")
    async def complete_run(self, run_id: str, outcome: str | None = None) -> AgentRun | None:
        run = self._runs.get(run_id)
        if run is None:
            return None
        from datetime import UTC, datetime

        run.status = RunStatus.COMPLETED
        run.ended_at = datetime.now(UTC)
        run.outcome = outcome
        run.total_steps = len(self._steps.get(run_id, []))
        await self._publish_agent_event("AGENT_RUN_COMPLETED", run_id, run.model_dump(mode="json"))
        logger.info("Run completed run_id=%s outcome=%s", run_id, outcome)
        return run

    @timed("agent.fail_run")
    async def fail_run(self, run_id: str, error: str | None = None) -> AgentRun | None:
        run = self._runs.get(run_id)
        if run is None:
            return None
        from datetime import UTC, datetime

        run.status = RunStatus.FAILED
        run.ended_at = datetime.now(UTC)
        run.outcome = error
        await self._publish_agent_event("AGENT_RUN_FAILED", run_id, run.model_dump(mode="json"))
        logger.info("Run failed run_id=%s error=%s", run_id, error)
        return run

    @timed("agent.record_step")
    async def record_step(self, step: AgentStep) -> AgentStep:
        if step.run_id not in self._steps:
            self._steps[step.run_id] = []
        self._steps[step.run_id].append(step)

        run = self._runs.get(step.run_id)
        if run:
            run.total_tokens += step.input_tokens + step.output_tokens

        await self._publish_agent_event(
            f"AGENT_{step.step_type.value.upper()}",
            step.run_id,
            step.model_dump(mode="json"),
        )
        logger.debug("Step recorded run_id=%s step_type=%s", step.run_id, step.step_type)
        return step

    @timed("agent.get_trajectory")
    async def get_trajectory(self, run_id: str) -> AgentTrajectory | None:
        run = self._runs.get(run_id)
        if run is None:
            return None

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

    def get_runs(
        self,
        agent_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
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

    def get_run(self, run_id: str) -> AgentRun | None:
        return self._runs.get(run_id)

    def get_evaluations(
        self,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
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

    def get_evaluation_by_run_id(self, run_id: str) -> AgentEvaluation | None:
        return self._evaluations.get(run_id)

    async def export_training_dataset(
        self,
        run_ids: list[str] | None = None,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        entries = []
        target_runs = (
            list(self._runs.values())
            if run_ids is None
            else [self._runs[rid] for rid in run_ids if rid in self._runs]
        )

        for run in target_runs:
            trajectory = await self.get_trajectory(run.run_id)
            if trajectory is None:
                continue

            evaluation = self._evaluations.get(run.run_id)
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
