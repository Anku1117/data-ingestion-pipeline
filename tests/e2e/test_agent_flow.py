from __future__ import annotations

import pytest

from services.agent_data.models import AgentRun, AgentStep, AgentTask, StepType
from services.agent_data.service import AgentDataService
from services.detector.engine import DetectionEngine


@pytest.fixture
def agent_service() -> AgentDataService:
    return AgentDataService()


@pytest.fixture
def detection_engine() -> DetectionEngine:
    return DetectionEngine()


@pytest.mark.asyncio
class TestE2EAgentFlow:
    """End-to-end: Agent events -> trajectory -> evaluation."""

    async def test_agent_task_to_trajectory(self, agent_service: AgentDataService) -> None:
        task = AgentTask(description="Test task", agent_id="agent_1")
        await agent_service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_1")
        await agent_service.start_run(run)

        step1 = AgentStep(
            run_id=run.run_id, step_number=1, step_type=StepType.MODEL_CALL,
            model_id="gpt-4", input_tokens=100, output_tokens=50, latency_ms=500,
        )
        await agent_service.record_step(step1)

        step2 = AgentStep(
            run_id=run.run_id, step_number=2, step_type=StepType.TOOL_CALL,
            tool_name="search", tool_status="success", latency_ms=200,
        )
        await agent_service.record_step(step2)

        step3 = AgentStep(
            run_id=run.run_id, step_number=3, step_type=StepType.MODEL_CALL,
            model_id="gpt-4", input_tokens=80, output_tokens=30, latency_ms=400,
        )
        await agent_service.record_step(step3)

        await agent_service.complete_run(run.run_id, outcome="Task completed successfully")

        trajectory = await agent_service.get_trajectory(run.run_id)
        assert trajectory is not None
        assert len(trajectory.steps) == 3
        assert trajectory.total_tokens == 260
        assert trajectory.outcome == "Task completed successfully"

    async def test_agent_evaluation(self, agent_service: AgentDataService) -> None:
        task = AgentTask(description="Eval task", agent_id="agent_2")
        await agent_service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_2")
        await agent_service.start_run(run)
        await agent_service.complete_run(run.run_id, outcome="success")

        from services.agent_data.models import AgentEvaluation
        evaluation = AgentEvaluation(
            run_id=run.run_id, agent_id="agent_2",
            success=True, score=0.85, total_tokens=200,
        )
        await agent_service.create_evaluation(evaluation)

        evals = agent_service.get_evaluations(agent_id="agent_2")
        assert evals["total"] == 1
        assert evals["evaluations"][0]["score"] == 0.85

    async def test_export_training_data(self, agent_service: AgentDataService) -> None:
        task = AgentTask(description="Export task", agent_id="agent_3")
        await agent_service.create_task(task)

        run = AgentRun(task_id=task.task_id, agent_id="agent_3")
        await agent_service.start_run(run)

        step = AgentStep(
            run_id=run.run_id, step_number=1, step_type=StepType.MODEL_CALL,
            model_id="gpt-4", input_tokens=50, output_tokens=25,
        )
        await agent_service.record_step(step)
        await agent_service.complete_run(run.run_id, outcome="done")

        from services.agent_data.models import AgentEvaluation
        evaluation = AgentEvaluation(
            run_id=run.run_id, agent_id="agent_3",
            success=True, score=0.90,
        )
        await agent_service.create_evaluation(evaluation)

        dataset = await agent_service.export_training_dataset(min_score=0.8)
        assert len(dataset) == 1
        assert dataset[0]["run_id"] == run.run_id
        assert "trajectory" in dataset[0]


@pytest.mark.asyncio
class TestE2EThreatDetection:
    """End-to-end: Security events -> detection -> threat alerts."""

    async def test_brute_force_detection(self, detection_engine: DetectionEngine) -> None:
        events = [
            {
                "event_id": f"evt_{i}",
                "event_type": "LOGIN_FAILED",
                "source": "auth_service",
                "payload": {"user_id": "u1"},
            }
            for i in range(10)
        ]
        results = detection_engine.evaluate(events)
        assert any(r.detected for r in results)

        alerts = detection_engine.get_alerts()
        assert alerts["total"] > 0

    async def test_port_scan_detection(self, detection_engine: DetectionEngine) -> None:
        events = [
            {"event_id": f"evt_{i}", "event_type": "NETWORK_CONNECTION", "source": "network",
             "payload": {"source_ip": "192.168.1.1", "dest_port": str(1000 + i)}}
            for i in range(15)
        ]
        results = detection_engine.evaluate(events)
        assert any(r.detected for r in results)

    async def test_detection_rules_list(self, detection_engine: DetectionEngine) -> None:
        rules = detection_engine.get_rules()
        assert len(rules) > 0
        assert all("name" in r and "description" in r for r in rules)

    async def test_detection_stats(self, detection_engine: DetectionEngine) -> None:
        stats = detection_engine.get_stats()
        assert "total_alerts" in stats
        assert "active_rules" in stats
        assert "rules" in stats
