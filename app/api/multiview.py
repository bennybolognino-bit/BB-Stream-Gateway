from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.decoder_manager import decoder_manager
from app.services.multiview_manager import multiview_manager

router = APIRouter(
    prefix="/api/multiview",
    tags=["Multiview"]
)


class MultiviewConfiguration(BaseModel):
    layout: int = Field(default=2, ge=2, le=4)


@router.get("/status")
def status():
    return multiview_manager.status()


@router.post("/start")
def start(configuration: MultiviewConfiguration):
    try:
        return multiview_manager.start(
            decoder_manager.list_channels(),
            configuration.layout
        )
    except (RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/stop")
def stop():
    return multiview_manager.stop()
