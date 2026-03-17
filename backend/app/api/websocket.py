from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.dependencies import get_simulation_service
from app.services.simulation_service import SimulationService


router = APIRouter(tags=["websocket"])


@router.websocket("/ws/metrics")
async def metrics_stream(
    websocket: WebSocket,
    service: SimulationService = Depends(get_simulation_service),
) -> None:
    await websocket.accept()
    queue = await service.subscribe()
    try:
        while True:
            frame = await queue.get()
            await websocket.send_json(frame)
    except (WebSocketDisconnect, asyncio.CancelledError):
        service.unsubscribe(queue)
