from app.services.process_manager import ProcessManager

DEFAULT_ENCODERS = [
    {
        "id": number,
        "name": f"Encoder {number}",
        "input_type": "srt",
        "input_url": "",
        "output_url": "",
        "video_mode": "copy",
        "video_bitrate": "6M",
        "audio_mode": "copy"
    }
    for number in range(1, 5)
]


class EncoderManager(ProcessManager):
    VIDEO_CODECS = {
        "copy": "copy",
        "h264_qsv": "h264_qsv",
        "hevc_qsv": "hevc_qsv",
        "libx264": "libx264",
        "libx265": "libx265"
    }

    OUTPUT_FORMATS = {
        "srt": "mpegts",
        "udp": "mpegts",
        "rtp": "rtp_mpegts",
        "rtmp": "flv",
        "rtmps": "flv"
    }

    def build_command(self, channel):
        input_url = channel["input_url"].strip()
        output_url = channel["output_url"].strip()
        video_mode = channel["video_mode"]

        if not input_url or not output_url:
            raise ValueError("Input and output URLs are required")

        if video_mode not in self.VIDEO_CODECS:
            raise ValueError("Unsupported video codec")

        protocol = output_url.split(":", 1)[0].lower()

        if protocol not in self.OUTPUT_FORMATS:
            raise ValueError("Unsupported output protocol")

        command = [
            "ffmpeg",
            "-hide_banner",
            "-nostdin",
            "-loglevel", "warning",
            "-i", input_url,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c:v", self.VIDEO_CODECS[video_mode]
        ]

        if video_mode != "copy":
            command.extend([
                "-b:v", channel.get("video_bitrate", "6M")
            ])

        audio_mode = channel.get("audio_mode", "copy")
        command.extend(["-c:a", audio_mode])

        if audio_mode == "aac":
            command.extend(["-b:a", "192k"])

        command.extend([
            "-f", self.OUTPUT_FORMATS[protocol],
            output_url
        ])

        return command


encoder_manager = EncoderManager(
    data_file="data/encoders.json",
    log_prefix="encoder",
    defaults=DEFAULT_ENCODERS
)


