from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_simulation_service
from app.api.schemas import UploadResponse
from app.services.simulation_service import SimulationService


router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.get("/export")
async def export_dataset(
    service: SimulationService = Depends(get_simulation_service),
) -> StreamingResponse:
    csv_payload = service.trace_service.export_csv()
    return StreamingResponse(
        iter([csv_payload]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=side_channel_dataset.csv"},
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    source: str = Form(default="ascad"),
    service: SimulationService = Depends(get_simulation_service),
) -> UploadResponse:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported.")
    content = await file.read()
    dataframe = pd.read_csv(BytesIO(content))
    imported = service.trace_service.import_dataframe(dataframe, source=source)
    return UploadResponse(imported_rows=imported, source=source)
