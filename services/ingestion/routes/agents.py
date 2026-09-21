from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from libraries.logging.logging import get_logger
from services.agent_data.service import AgentDataService

logger = get_logger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])

_agent_service: AgentDataService | None = None


def _get_service() -> AgentDataService:
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentDataService()
    return _agent_service


@router.get("/runs")
async def list_runs(
    agent_id: str | None = Query(None, description="Filter by agent ID"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    service = _get_service()
    return service.get_runs(agent_id=agent_id, status=status, limit=limit, offset=offset)


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    service = _get_service()
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "detail": f"Run {run_id} not found"},
        )
    return run.model_dump(mode="json")


@router.get("/runs/{run_id}/trajectory")
async def get_trajectory(run_id: str) -> dict:
    service = _get_service()
    trajectory = await service.get_trajectory(run_id)
    if trajectory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "detail": f"Trajectory for run {run_id} not found"},
        )
    return trajectory.model_dump(mode="json")


@router.get("/evaluations")
async def list_evaluations(
    agent_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    service = _get_service()
    return service.get_evaluations(agent_id=agent_id, limit=limit, offset=offset)


@router.get("/evaluations/{run_id}")
async def get_evaluation(run_id: str) -> dict:
    service = _get_service()
    evaluation = service.get_evaluation_by_run_id(run_id)
    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "detail": f"Evaluation for run {run_id} not found"},
        )
    return evaluation.model_dump(mode="json")
