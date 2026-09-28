import math
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
        self.layout = "grid2"
        self.custom_columns = 2
        self.tiles = []

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
            raise RuntimeError("MediaMTX executable not found")

        self.server_log = Path("logs/mediamtx.log").open(
            "a",
            encoding="utf-8"
        )

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

    def _grid(self, columns, rows):
        tile_width = 1280 // columns
        tile_height = 720 // rows
        positions = []

        for row in range(rows):
            for column in range(columns):
                positions.append({
                    "x": column * tile_width,
                    "y": row * tile_height,
                    "width": tile_width,
                    "height": tile_height
                })

        return positions

    def _layout_positions(
        self,
        layout,
        channel_count,
        custom_columns
    ):
        if layout == "grid2":
            return self._grid(2, 2)

        if layout == "grid3":
            return self._grid(3, 3)

        if layout == "grid4":
            return self._grid(4, 4)

        if layout == "main3":
            return [
                {
                    "x": 0,
                    "y": 0,
                    "width": 960,
                    "height": 720
                },
                {
                    "x": 960,
                    "y": 0,
                    "width": 320,
                    "height": 240
                },
                {
                    "x": 960,
                    "y": 240,
                    "width": 320,
                    "height": 240
                },
                {
                    "x": 960,
                    "y": 480,
                    "width": 320,
                    "height": 240
                }
            ]

        if layout == "main5":
            positions = [{
                "x": 0,
                "y": 0,
                "width": 960,
                "height": 720
            }]

            for row in range(5):
                positions.append({
                    "x": 960,
                    "y": row * 144,
                    "width": 320,
                    "height": 144
                })

            return positions

        if layout == "custom":
            count = max(1, min(channel_count, 16))
            columns = max(1, min(custom_columns, count, 4))
            rows = math.ceil(count / columns)

            positions = self._grid(columns, rows)
            return positions[:count]

        raise ValueError("Unsupported multiview layout")

    def _ordered_channels(self, channels, channel_ids):
        configured = [
            channel for channel in channels
            if channel.get("input_url", "").strip()
        ]

        if not channel_ids:
            return configured

        lookup = {
            channel["id"]: channel
            for channel in configured
        }

        ordered = []

        for channel_id in channel_ids:
            channel = lookup.get(channel_id)

            if channel:
                ordered.append(channel)

        return ordered

    def build_command(self, channels, positions):
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
                "-fflags", "+genpts+discardcorrupt",
                "-use_wallclock_as_timestamps", "1",
                "-thread_queue_size", "1024",
                "-i", channel["input_url"]
            ])

        for index in range(len(channels), len(positions)):
            position = positions[index]

            command.extend([
                "-f", "lavfi",
                "-i",
                (
                    "color=c=black:"
                    f"s={position['width']}x"
                    f"{position['height']}:r=25"
                )
            ])

        filters = []
        labels = []

        for index, position in enumerate(positions):
            width = position["width"]
            height = position["height"]

            filters.append(
                f"[{index}:v]"
                f"settb=AVTB,setpts=N/(25*TB),fps=25,"
                f"scale={width}:{height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:"
                f"(ow-iw)/2:(oh-ih)/2:black,"
                f"setsar=1,"
                f"setpts=PTS"
                f"[v{index}]"
            )

            labels.append(f"[v{index}]")

        layout_string = "|".join(
            f"{position['x']}_{position['y']}"
            for position in positions
        )

        filters.append(
            "".join(labels) +
            f"xstack=inputs={len(positions)}:"
            f"layout={layout_string}:fill=black,"
            f"pad=1280:720:0:0:black[outv]"
        )

        command.extend([
            "-filter_complex", ";".join(filters),
            "-map", "[outv]",
            "-an",
            "-r", "25",
            "-fps_mode", "cfr",
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

    def start(
        self,
        channels,
        layout,
        channel_ids,
        custom_columns
    ):
        ordered = self._ordered_channels(
            channels,
            channel_ids
        )

        if not ordered:
            raise RuntimeError("No configured decoder inputs")

        positions = self._layout_positions(
            layout,
            len(ordered),
            custom_columns
        )

        ordered = ordered[:len(positions)]

        self._stop_mosaic()
        self.ensure_mediamtx()

        self.process_log = Path(
            "logs/multiview-webrtc.log"
        ).open("a", encoding="utf-8")

        self.process = subprocess.Popen(
            self.build_command(ordered, positions),
            stdout=self.process_log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0
            )
        )

        self.layout = layout
        self.custom_columns = custom_columns
        self.tiles = []

        for index, position in enumerate(positions):
            channel = (
                ordered[index]
                if index < len(ordered)
                else None
            )

            self.tiles.append({
                **position,
                "id": channel["id"] if channel else None,
                "name": channel["name"] if channel else "NO SIGNAL"
            })

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
        self.tiles = []
        return self.status()

    def status(self):
        running = (
            self.process is not None
            and self.process.poll() is None
        )

        return {
            "running": running,
            "layout": self.layout,
            "custom_columns": self.custom_columns,
            "tiles": self.tiles if running else [],
            "webrtc_url": (
                "http://127.0.0.1:8889/multiview"
                if running else None
            )
        }


multiview_manager = MultiviewManager()


