import subprocess

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.decoder_manager import decoder_manager

router = APIRouter(
    prefix="/api/multiview",
    tags=["Multiview"]
)


def generate_preview(input_url):
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", "error",
        "-fflags", "nobuffer",
        "-i", input_url,
        "-an",
        "-vf", "fps=8,scale=640:-2",
        "-c:v", "mjpeg",
        "-q:v", "7",
        "-f", "mpjpeg",
        "-boundary_tag", "frame",
        "pipe:1"
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0
        )
    )

    try:
        while True:
            chunk = process.stdout.read(32768)

            if not chunk:
                break

            yield chunk
    finally:
        if process.poll() is None:
            process.terminate()

            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()


@router.get("/preview/{channel_id}")
def preview(channel_id: int):
    channel = decoder_manager.get_channel(channel_id)

    if channel is None:
        raise HTTPException(
            status_code=404,
            detail="Decoder not found"
        )

    input_url = channel.get("input_url", "").strip()

    if not input_url:
        raise HTTPException(
            status_code=400,
            detail="Decoder input is not configured"
        )

    return StreamingResponse(
        generate_preview(input_url),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-store, no-cache",
            "Pragma": "no-cache"
        }
    )
