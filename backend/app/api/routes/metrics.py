from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_simulation_service
from app.services.simulation_service import SimulationService


router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/current")
async def current_metrics(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    return service.current_metrics()


@router.get("/history")
async def metrics_history(
    limit: int = Query(default=40, ge=1, le=200),
    service: SimulationService = Depends(get_simulation_service),
) -> list[dict]:
    return service.history(limit)
