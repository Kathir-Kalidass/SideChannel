from fastapi import APIRouter, Depends

from app.api.dependencies import get_simulation_service
from app.api.schemas import ManualDefenseRequest
from app.services.simulation_service import SimulationService


router = APIRouter(prefix="/defense", tags=["defense"])


@router.get("/status")
async def defense_status(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    return service.defense_status()


@router.post("/activate")
async def activate_defense(
    payload: ManualDefenseRequest,
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    details = await service.activate_defense(payload.technique)
    return {"status": "defense_activated", "details": details}


@router.post("/disable")
async def disable_defense(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    details = await service.disable_defense()
    return {"status": "defense_disabled", "details": details}
