import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path
from multiprocessing import freeze_support


def application_directory():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def port_is_open(port):
    try:
        with socket.create_connection(
            ("127.0.0.1", port),
            timeout=0.3
        ):
            return True
    except OSError:
        return False


def open_browser():
    webbrowser.open("http://127.0.0.1:8080")


def main():
    base_directory = application_directory()
    os.chdir(base_directory)

    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    ffmpeg_directory = base_directory / "tools" / "ffmpeg"

    os.environ["PATH"] = (
        str(ffmpeg_directory)
        + os.pathsep
        + os.environ.get("PATH", "")
    )

    if port_is_open(8080):
        open_browser()
        return

    from app.main import app
    import uvicorn

    threading.Timer(1.5, open_browser).start()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        log_level="info"
    )


if __name__ == "__main__":
    freeze_support()
    main()
