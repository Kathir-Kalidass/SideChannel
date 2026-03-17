from fastapi import APIRouter, Depends

from app.api.dependencies import get_simulation_service
from app.services.simulation_service import SimulationService


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/prediction")
async def ai_prediction(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    return service.ai_prediction()


@router.post("/train")
async def train_ai(
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    return await service.train_model()
