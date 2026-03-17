from fastapi import APIRouter, Depends

from app.api.dependencies import get_simulation_service
from app.api.schemas import SimulationConfig
from app.services.simulation_service import SimulationService


router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/start")
async def start_simulation(
    config: SimulationConfig,
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    status = await service.start(config.model_dump())
    return {
        "status": "simulation_started",
        "simulation_id": status["simulation_id"],
        "details": status,
    }


@router.post("/stop")
async def stop_simulation(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    status = await service.stop()
    return {"status": "simulation_stopped", "details": status}


@router.post("/reset")
async def reset_simulation(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    status = await service.reset()
    return {"status": "simulation_reset", "details": status}


@router.get("/status")
async def simulation_status(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    return service.status()
