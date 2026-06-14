from __future__ import annotations

import subprocess
from pathlib import Path


def extract_audio_sample(audio_url: str, output_path: Path, seconds: float) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        audio_url,
        "-t",
        str(seconds),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg failed to extract audio sample")
    return output_path
