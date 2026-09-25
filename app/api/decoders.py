from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.decoder_manager import decoder_manager

router = APIRouter(prefix="/api/decoders", tags=["Decoders"])


class DecoderConfiguration(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    input_type: Literal["srt", "rtmp", "rtsp", "rtp", "udp", "hls", "http", "file", "smpte2022"] = "srt"
    input_url: str
    display_mode: Literal["window", "fullscreen"] = "window"
    hardware_acceleration: bool = True


@router.post("")
def create_decoder():
    try:
        return decoder_manager.create_channel()
    except RuntimeError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.delete("/{channel_id}")
def delete_decoder(channel_id: int):
    try:
        return decoder_manager.delete_channel(channel_id)
    except (KeyError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.get("")
def list_decoders():
    return decoder_manager.list_channels()


@router.put("/{channel_id}")
def update_decoder(
    channel_id: int,
    configuration: DecoderConfiguration
):
    try:
        return decoder_manager.update_channel(
            channel_id,
            configuration.model_dump()
        )
    except (KeyError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{channel_id}/start")
def start_decoder(channel_id: int):
    try:
        return decoder_manager.start(channel_id)
    except (KeyError, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{channel_id}/stop")
def stop_decoder(channel_id: int):
    return decoder_manager.stop(channel_id)


