from fastapi import APIRouter, Depends

from app.api.dependencies import get_simulation_service
from app.services.simulation_service import SimulationService


router = APIRouter(prefix="/attack", tags=["attack"])


@router.post("/start")
async def start_attack(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    status = await service.start_attack()
    return {"status": "attack_started", "details": status}


@router.get("/status")
async def attack_status(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    return service.attack_status()


@router.get("/log")
async def attack_log(
    service: SimulationService = Depends(get_simulation_service),
) -> list[str]:
    return service.event_log()
