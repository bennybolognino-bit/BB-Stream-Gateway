import json
import subprocess
import threading
from pathlib import Path

DATA_FILE = Path("data/channels.json")
LOG_DIRECTORY = Path("logs")

DEFAULT_CHANNELS = [
    {
        "id": number,
        "name": f"Channel {number}",
        "input_url": "",
        "output_url": "",
        "video_mode": "copy",
        "audio_mode": "copy"
    }
    for number in range(1, 5)
]


class ChannelManager:
    def __init__(self):
        self.processes = {}
        self.logs = {}
        self.lock = threading.Lock()

        DATA_FILE.parent.mkdir(exist_ok=True)
        LOG_DIRECTORY.mkdir(exist_ok=True)

        if not DATA_FILE.exists():
            self._save(DEFAULT_CHANNELS)

    def _load(self):
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))

    def _save(self, channels):
        DATA_FILE.write_text(
            json.dumps(channels, indent=2),
            encoding="utf-8"
        )

    def is_running(self, channel_id):
        process = self.processes.get(channel_id)
        return process is not None and process.poll() is None

    def list_channels(self):
        channels = self._load()

        for channel in channels:
            channel["running"] = self.is_running(channel["id"])

        return channels

    def get_channel(self, channel_id):
        return next(
            (item for item in self._load() if item["id"] == channel_id),
            None
        )

    def update_channel(self, channel_id, configuration):
        if self.is_running(channel_id):
            raise RuntimeError("Stop the channel before changing it")

        channels = self._load()

        for index, channel in enumerate(channels):
            if channel["id"] == channel_id:
                configuration["id"] = channel_id
                channels[index] = configuration
                self._save(channels)
                return configuration

        raise KeyError("Channel not found")

    def _video_codec(self, mode):
        codecs = {
            "copy": "copy",
            "h264_qsv": "h264_qsv",
            "hevc_qsv": "hevc_qsv",
            "libx264": "libx264",
            "libx265": "libx265"
        }

        if mode not in codecs:
            raise ValueError("Unsupported video mode")

        return codecs[mode]

    def _output_format(self, output_url):
        protocol = output_url.split(":", 1)[0].lower()

        formats = {
            "srt": "mpegts",
            "udp": "mpegts",
            "rtp": "rtp_mpegts",
            "rtmp": "flv",
            "rtmps": "flv"
        }

        if protocol not in formats:
            raise ValueError(f"Unsupported output protocol: {protocol}")

        return formats[protocol]

    def build_command(self, channel):
        if not channel["input_url"] or not channel["output_url"]:
            raise ValueError("Input and output URLs are required")

        return [
            "ffmpeg",
            "-hide_banner",
            "-nostdin",
            "-loglevel", "warning",
            "-i", channel["input_url"],
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c:v", self._video_codec(channel["video_mode"]),
            "-c:a", channel.get("audio_mode", "copy"),
            "-f", self._output_format(channel["output_url"]),
            channel["output_url"]
        ]

    def start(self, channel_id):
        with self.lock:
            if self.is_running(channel_id):
                raise RuntimeError("Channel already running")

            channel = self.get_channel(channel_id)

            if channel is None:
                raise KeyError("Channel not found")

            log_file = (LOG_DIRECTORY / f"channel-{channel_id}.log").open(
                "a",
                encoding="utf-8"
            )

            process = subprocess.Popen(
                self.build_command(channel),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            self.processes[channel_id] = process
            self.logs[channel_id] = log_file

            return {
                "channel_id": channel_id,
                "running": True,
                "pid": process.pid
            }

    def stop(self, channel_id):
        with self.lock:
            process = self.processes.pop(channel_id, None)

            if process and process.poll() is None:
                process.terminate()

                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

            log_file = self.logs.pop(channel_id, None)

            if log_file:
                log_file.close()

            return {"channel_id": channel_id, "running": False}


channel_manager = ChannelManager()
