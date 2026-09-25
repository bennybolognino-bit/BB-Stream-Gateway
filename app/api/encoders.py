from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.encoder_manager import encoder_manager

router = APIRouter(prefix="/api/encoders", tags=["Encoders"])


class EncoderConfiguration(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    input_type: Literal["srt", "rtmp", "rtsp", "rtp", "udp", "hls", "http", "file", "smpte2022"] = "srt"
    input_url: str
    output_url: str
    video_mode: Literal[
        "copy",
        "h264_qsv",
        "hevc_qsv",
        "libx264",
        "libx265"
    ] = "copy"
    video_bitrate: str = "6M"
    audio_mode: Literal["copy", "aac"] = "copy"


@router.post("")
def create_encoder():
    try:
        return encoder_manager.create_channel()
    except RuntimeError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.delete("/{channel_id}")
def delete_encoder(channel_id: int):
    try:
        return encoder_manager.delete_channel(channel_id)
    except (KeyError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.get("")
def list_encoders():
    return encoder_manager.list_channels()


@router.put("/{channel_id}")
def update_encoder(
    channel_id: int,
    configuration: EncoderConfiguration
):
    try:
        return encoder_manager.update_channel(
            channel_id,
            configuration.model_dump()
        )
    except (KeyError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{channel_id}/start")
def start_encoder(channel_id: int):
    try:
        return encoder_manager.start(channel_id)
    except (KeyError, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{channel_id}/stop")
def stop_encoder(channel_id: int):
    return encoder_manager.stop(channel_id)


