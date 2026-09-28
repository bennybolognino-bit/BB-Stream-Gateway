import socket
import subprocess
import time
from pathlib import Path


class MultiviewManager:
    def __init__(self):
        self.process = None
        self.process_log = None
        self.server_process = None
        self.server_log = None
        self.layout = 2
        self.channels = []

    def _port_open(self, port):
        try:
            with socket.create_connection(
                ("127.0.0.1", port),
                timeout=0.3
            ):
                return True
        except OSError:
            return False

    def ensure_mediamtx(self):
        if self._port_open(8554) and self._port_open(8889):
            return

        executable = Path(
            "tools/mediamtx/mediamtx.exe"
        ).resolve()

        if not executable.exists():
            raise RuntimeError(
                "MediaMTX executable not found"
            )

        self.server_log = Path(
            "logs/mediamtx.log"
        ).open("a", encoding="utf-8")

        self.server_process = subprocess.Popen(
            [str(executable)],
            cwd=str(executable.parent),
            stdout=self.server_log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0
            )
        )

        for _ in range(30):
            if self._port_open(8554) and self._port_open(8889):
                return

            if self.server_process.poll() is not None:
                break

            time.sleep(0.25)

        raise RuntimeError(
            "MediaMTX did not start; check logs/mediamtx.log"
        )

    def _stop_mosaic(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)

        self.process = None

        if self.process_log:
            self.process_log.close()
            self.process_log = None

    def _tile_size(self, columns):
        sizes = {
            2: (640, 360),
            3: (426, 240),
            4: (320, 180)
        }
        return sizes[columns]

    def build_command(self, channels, columns):
        slots = columns * columns
        tile_width, tile_height = self._tile_size(columns)

        command = [
            "ffmpeg",
            "-hide_banner",
            "-nostdin",
            "-loglevel", "warning"
        ]

        for channel in channels:
            if channel.get("input_type") == "file":
                command.append("-re")

            command.extend([
                "-thread_queue_size", "512",
                "-i", channel["input_url"]
            ])

        for _ in range(slots - len(channels)):
            command.extend([
                "-f", "lavfi",
                "-i",
                (
                    f"color=c=black:"
                    f"s={tile_width}x{tile_height}:r=25"
                )
            ])

        filters = []
        labels = []

        for index in range(slots):
            filters.append(
                f"[{index}:v]"
                f"fps=25,"
                f"scale={tile_width}:{tile_height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={tile_width}:{tile_height}:"
                f"(ow-iw)/2:(oh-ih)/2:black,"
                f"setsar=1,"
                f"setpts=PTS-STARTPTS"
                f"[v{index}]"
            )
            labels.append(f"[v{index}]")

        positions = []

        for index in range(slots):
            column = index % columns
            row = index // columns
            positions.append(
                f"{column * tile_width}_{row * tile_height}"
            )

        filters.append(
            "".join(labels) +
            f"xstack=inputs={slots}:"
            f"layout={'|'.join(positions)}:"
            f"fill=black[outv]"
        )

        command.extend([
            "-filter_complex", ";".join(filters),
            "-map", "[outv]",
            "-an",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-profile:v", "baseline",
            "-level", "3.1",
            "-pix_fmt", "yuv420p",
            "-bf", "0",
            "-g", "25",
            "-keyint_min", "25",
            "-b:v", "4500k",
            "-maxrate", "5000k",
            "-bufsize", "2500k",
            "-rtsp_transport", "tcp",
            "-f", "rtsp",
            "rtsp://127.0.0.1:8554/multiview"
        ])

        return command

    def start(self, channels, columns):
        if columns not in (2, 3, 4):
            raise ValueError("Layout must be 2, 3 or 4")

        configured = [
            channel for channel in channels
            if channel.get("input_url", "").strip()
        ]

        slots = columns * columns
        configured = configured[:slots]

        if not configured:
            raise RuntimeError(
                "No configured decoder inputs"
            )

        self._stop_mosaic()
        self.ensure_mediamtx()

        self.process_log = Path(
            "logs/multiview-webrtc.log"
        ).open("a", encoding="utf-8")

        self.process = subprocess.Popen(
            self.build_command(configured, columns),
            stdout=self.process_log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0
            )
        )

        self.layout = columns
        self.channels = [
            {
                "id": channel["id"],
                "name": channel["name"]
            }
            for channel in configured
        ]

        time.sleep(0.7)

        if self.process.poll() is not None:
            self._stop_mosaic()
            raise RuntimeError(
                "Multiview failed; check "
                "logs/multiview-webrtc.log"
            )

        return self.status()

    def stop(self):
        self._stop_mosaic()
        self.channels = []
        return self.status()

    def status(self):
        running = (
            self.process is not None
            and self.process.poll() is None
        )

        return {
            "running": running,
            "layout": self.layout,
            "channels": self.channels if running else [],
            "webrtc_url":
                "http://127.0.0.1:8889/multiview"
                if running else None
        }


multiview_manager = MultiviewManager()
