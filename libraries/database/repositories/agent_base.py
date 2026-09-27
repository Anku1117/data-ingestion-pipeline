from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from services.agent_data.models import AgentEvaluation, AgentRun, AgentStep, AgentTask


class AgentRunRepository(ABC):
    @abstractmethod
    async def create(self, run: AgentRun) -> None: ...

    @abstractmethod
    async def get_by_id(self, run_id: str) -> AgentRun | None: ...

    @abstractmethod
    async def update(self, run: AgentRun) -> None: ...

    @abstractmethod
    async def list_runs(
        self,
        agent_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def count_steps(self, run_id: str) -> int: ...


class AgentStepRepository(ABC):
    @abstractmethod
    async def create(self, step: AgentStep) -> None: ...

    @abstractmethod
    async def list_by_run(self, run_id: str) -> list[AgentStep]: ...

    @abstractmethod
    async def count_by_run(self, run_id: str) -> int: ...


class AgentEvaluationRepository(ABC):
    @abstractmethod
    async def create(self, evaluation: AgentEvaluation) -> None: ...

    @abstractmethod
    async def get_by_run_id(self, run_id: str) -> AgentEvaluation | None: ...

    @abstractmethod
    async def list_evaluations(
        self,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]: ...


class AgentTaskRepository(ABC):
    @abstractmethod
    async def create(self, task: AgentTask) -> None: ...

    @abstractmethod
    async def get_by_id(self, task_id: str) -> AgentTask | None: ...
