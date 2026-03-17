from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.attack_predictor import AttackPredictor
from app.api.routes import ai, attack, dataset, defense, metrics, payment, simulation
from app.api.websocket import router as websocket_router
from app.config import settings
from app.database import models
from app.database.db import database
from app.services.simulation_service import SimulationService
from app.services.trace_service import TraceService


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = models
    database.init(settings.database_url)
    database.create_tables()
    trace_service = TraceService()
    predictor = AttackPredictor(settings.model_path)
    simulation_service = SimulationService(settings, trace_service, predictor)
    await simulation_service.initialize()
    app.state.simulation_service = simulation_service
    yield
    await simulation_service.stop()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(simulation.router, prefix=settings.api_prefix)
    app.include_router(metrics.router, prefix=settings.api_prefix)
    app.include_router(attack.router, prefix=settings.api_prefix)
    app.include_router(ai.router, prefix=settings.api_prefix)
    app.include_router(defense.router, prefix=settings.api_prefix)
    app.include_router(dataset.router, prefix=settings.api_prefix)
    app.include_router(payment.router, prefix=settings.api_prefix)
    app.include_router(websocket_router, prefix=settings.api_prefix)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": settings.app_name}

    return app


app = create_app()
