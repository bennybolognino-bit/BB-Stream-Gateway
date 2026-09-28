import threading
import time

import comtypes
from pycaw.pycaw import AudioUtilities

from app.services.process_manager import ProcessManager

DEFAULT_DECODERS = [
    {
        "id": number,
        "name": f"Decoder {number}",
        "input_type": "srt",
        "input_url": "",
        "display_mode": "window",
        "hardware_acceleration": True,
        "volume": 100,
        "muted": False
    }
    for number in range(1, 5)
]


class DecoderManager(ProcessManager):
    def update_channel(self, channel_id, configuration):
        current = self.get_channel(channel_id)

        if current:
            configuration["volume"] = current.get("volume", 100)
            configuration["muted"] = current.get("muted", False)

        return super().update_channel(channel_id, configuration)

    def apply_audio(self, channel_id, volume, muted):
        process = self.processes.get(channel_id)

        if not process or process.poll() is not None:
            raise RuntimeError("Decoder is not running")

        comtypes.CoInitialize()

        try:
            session = AudioUtilities.GetProcessSession(process.pid)

            if session is None:
                raise RuntimeError(
                    "Audio session is not ready yet"
                )

            audio = session.SimpleAudioVolume
            audio.SetMasterVolume(volume / 100.0, None)
            audio.SetMute(1 if muted else 0, None)
        finally:
            comtypes.CoUninitialize()

    def _apply_audio_with_retry(self, channel_id, volume, muted):
        for _ in range(20):
            try:
                self.apply_audio(channel_id, volume, muted)
                return
            except Exception:
                time.sleep(0.25)

    def set_audio(self, channel_id, volume, muted):
        volume = max(0, min(100, int(volume)))

        with self.lock:
            channels = self._load()
            found = False

            for channel in channels:
                if channel["id"] == channel_id:
                    channel["volume"] = volume
                    channel["muted"] = bool(muted)
                    found = True
                    break

            if not found:
                raise KeyError("Channel not found")

            self._save(channels)

        if self.is_running(channel_id):
            self.apply_audio(channel_id, volume, muted)

        return {
            "channel_id": channel_id,
            "volume": volume,
            "muted": bool(muted),
            "running": self.is_running(channel_id)
        }

    def start(self, channel_id):
        result = super().start(channel_id)
        channel = self.get_channel(channel_id)

        thread = threading.Thread(
            target=self._apply_audio_with_retry,
            args=(
                channel_id,
                channel.get("volume", 100),
                channel.get("muted", False)
            ),
            daemon=True
        )
        thread.start()

        return result
    def build_command(self, channel):
        input_url = channel["input_url"].strip()

        if not input_url:
            raise ValueError("Input URL is required")

        command = [
            "ffplay",
            "-hide_banner",
            "-loglevel", "warning",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-framedrop",
            "-window_title", channel["name"]
        ]

        if channel.get("hardware_acceleration", True):
            command.extend(["-hwaccel", "auto"])

        if channel.get("display_mode") == "fullscreen":
            command.append("-fs")

        command.append(input_url)
        return command


decoder_manager = DecoderManager(
    data_file="data/decoders.json",
    log_prefix="decoder",
    defaults=DEFAULT_DECODERS
)


