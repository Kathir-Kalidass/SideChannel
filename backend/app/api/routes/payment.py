from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_simulation_service
from app.api.schemas import LoginRequest, PaymentHistoryRequest
from app.services.simulation_service import SimulationService


router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/users")
async def list_users(
    service: SimulationService = Depends(get_simulation_service),
) -> list[dict]:
    return service.trace_service.list_payment_users()


@router.post("/login")
async def login(
    payload: LoginRequest,
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    user = service.trace_service.authenticate_payment_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user": user}


@router.get("/history")
async def payment_history(
    limit: int = Query(default=100, ge=1, le=500),
    service: SimulationService = Depends(get_simulation_service),
) -> list[dict]:
    return service.trace_service.payment_history(limit)


@router.post("/history")
async def create_payment_history(
    payload: PaymentHistoryRequest,
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    users = {user["id"]: user for user in service.trace_service.list_payment_users()}
    sender = users.get(payload.sender_user_id)
    receiver = users.get(payload.receiver_user_id)
    if sender is None or receiver is None:
        raise HTTPException(status_code=400, detail="Sender or receiver user does not exist")

    if sender["port"] != payload.sender_port or receiver["port"] != payload.receiver_port:
        raise HTTPException(status_code=400, detail="Port validation failed for sender or receiver")

    if sender["upi"] != payload.sender_upi or receiver["upi"] != payload.receiver_upi:
        raise HTTPException(status_code=400, detail="UPI validation failed for sender or receiver")

    if payload.sender_user_id == payload.receiver_user_id:
        raise HTTPException(status_code=400, detail="Sender and receiver cannot be the same")

    record = service.trace_service.save_payment_record(payload.model_dump())

    # Keep AI current as transaction history grows.
    await service.train_model()

    return {"status": "payment_saved", "record": record}


@router.get("/adaptive-policy")
async def adaptive_policy(
    sender_user_id: int = Query(..., ge=1),
    receiver_user_id: int = Query(..., ge=1),
    service: SimulationService = Depends(get_simulation_service),
) -> dict:
    users = {user["id"]: user for user in service.trace_service.list_payment_users()}
    if sender_user_id not in users or receiver_user_id not in users:
        raise HTTPException(status_code=400, detail="Sender or receiver user does not exist")
    return service.trace_service.get_adaptive_policy(sender_user_id, receiver_user_id)
