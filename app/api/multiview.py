from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.decoder_manager import decoder_manager
from app.services.multiview_manager import multiview_manager

router = APIRouter(
    prefix="/api/multiview",
    tags=["Multiview"]
)


class MultiviewConfiguration(BaseModel):
    layout: Literal[
        "grid2",
        "grid3",
        "grid4",
        "main3",
        "main5",
        "custom"
    ] = "grid2"
    custom_columns: int = Field(default=2, ge=1, le=4)
    channel_ids: list[int] = []


@router.get("/status")
def status():
    return multiview_manager.status()


@router.post("/start")
def start(configuration: MultiviewConfiguration):
    try:
        return multiview_manager.start(
            decoder_manager.list_channels(),
            configuration.layout,
            configuration.channel_ids,
            configuration.custom_columns
        )
    except (RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/stop")
def stop():
    return multiview_manager.stop()
