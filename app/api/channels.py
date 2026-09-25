from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.channel_manager import channel_manager

router = APIRouter(prefix="/api/channels", tags=["Channels"])


class ChannelConfiguration(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    input_url: str
    output_url: str
    video_mode: Literal[
        "copy",
        "h264_qsv",
        "hevc_qsv",
        "libx264",
        "libx265"
    ] = "copy"
    audio_mode: Literal["copy", "aac"] = "copy"


@router.get("")
def list_channels():
    return channel_manager.list_channels()


@router.put("/{channel_id}")
def update_channel(
    channel_id: int,
    configuration: ChannelConfiguration
):
    try:
        return channel_manager.update_channel(
            channel_id,
            configuration.model_dump()
        )
    except (KeyError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{channel_id}/start")
def start_channel(channel_id: int):
    try:
        return channel_manager.start(channel_id)
    except (KeyError, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{channel_id}/stop")
def stop_channel(channel_id: int):
    return channel_manager.stop(channel_id)
