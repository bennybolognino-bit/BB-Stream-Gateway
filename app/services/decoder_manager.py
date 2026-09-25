from app.services.process_manager import ProcessManager

DEFAULT_DECODERS = [
    {
        "id": number,
        "name": f"Decoder {number}",
        "input_type": "srt",
        "input_url": "",
        "display_mode": "window",
        "hardware_acceleration": True
    }
    for number in range(1, 5)
]


class DecoderManager(ProcessManager):
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

