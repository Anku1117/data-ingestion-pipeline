from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepType(str, Enum):
    MODEL_CALL = "model_call"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RETRIEVAL = "retrieval"
    MEMORY_OPERATION = "memory_operation"
    ENVIRONMENT_INTERACTION = "environment_interaction"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex}")
    description: str = ""
    agent_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex}")
    task_id: str
    agent_id: str
    session_id: str | None = None
    status: RunStatus = RunStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    outcome: str | None = None
    total_tokens: int = 0
    total_steps: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentStep(BaseModel):
    step_id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex}")
    run_id: str
    step_number: int
    step_type: StepType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_id: str | None = None
    parent_event_id: str | None = None
    model_id: str | None = None
    model_name: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    tool_name: str | None = None
    tool_status: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: dict[str, Any] | None = None
    retrieval_ids: list[str] = Field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTrajectory(BaseModel):
    run_id: str
    agent_id: str
    task_id: str
    steps: list[AgentStep] = Field(default_factory=list)
    outcome: str | None = None
    total_tokens: int = 0
    total_latency_ms: float = 0.0


class AgentEvaluation(BaseModel):
    evaluation_id: str = Field(default_factory=lambda: f"eval_{uuid.uuid4().hex}")
    run_id: str
    agent_id: str
    success: bool = False
    score: float = 0.0
    latency_ms: float = 0.0
    total_tokens: int = 0
    tool_failures: int = 0
    task_completion: float = 0.0
    anomaly_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TrainingDataset(BaseModel):
    dataset_id: str = Field(default_factory=lambda: f"dataset_{uuid.uuid4().hex}")
    version: str = "1.0"
    entries: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total_entries: int = 0
    quality_score: float | None = None
