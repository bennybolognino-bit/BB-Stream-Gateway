import json
import subprocess
import threading
from pathlib import Path


class ProcessManager:
    def __init__(self, data_file, log_prefix, defaults):
        self.data_file = Path(data_file)
        self.log_prefix = log_prefix
        self.defaults = defaults
        self.processes = {}
        self.log_files = {}
        self.lock = threading.Lock()

        self.data_file.parent.mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

        if not self.data_file.exists():
            self._save(defaults)

    def _load(self):
        return json.loads(self.data_file.read_text(encoding="utf-8-sig"))

    def _save(self, channels):
        self.data_file.write_text(
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
        with self.lock:
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

    def create_channel(self):
        with self.lock:
            channels = self._load()

            if len(channels) >= 16:
                raise RuntimeError("Maximum 16 channels")

            channel_id = max(
                (channel["id"] for channel in channels),
                default=0
            ) + 1

            channel = self.defaults[0].copy()
            channel["id"] = channel_id
            channel["name"] = (
                f"{self.log_prefix.capitalize()} {channel_id}"
            )

            channels.append(channel)
            self._save(channels)
            return channel

    def delete_channel(self, channel_id):
        with self.lock:
            if self.is_running(channel_id):
                raise RuntimeError(
                    "Stop the channel before deleting it"
                )

            channels = self._load()
            updated = [
                channel for channel in channels
                if channel["id"] != channel_id
            ]

            if len(updated) == len(channels):
                raise KeyError("Channel not found")

            self._save(updated)
            return {"channel_id": channel_id, "deleted": True}
    def build_command(self, channel):
        raise NotImplementedError

    def start(self, channel_id):
        with self.lock:
            if self.is_running(channel_id):
                raise RuntimeError("Channel already running")

            channel = self.get_channel(channel_id)

            if channel is None:
                raise KeyError("Channel not found")

            log_file = Path(
                f"logs/{self.log_prefix}-{channel_id}.log"
            ).open("a", encoding="utf-8")

            process = subprocess.Popen(
                self.build_command(channel),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                shell=False,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0
                )
            )

            self.processes[channel_id] = process
            self.log_files[channel_id] = log_file

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
                    process.wait(timeout=5)

            log_file = self.log_files.pop(channel_id, None)

            if log_file:
                log_file.close()

            return {
                "channel_id": channel_id,
                "running": False
            }


