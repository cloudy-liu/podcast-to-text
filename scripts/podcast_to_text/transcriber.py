from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .outputs import Segment


def transcribe_audio(
    audio_path: Path,
    *,
    model_name: str,
    device: str,
    compute_type: str,
    language: str,
    beam_size: int,
    vad_filter: bool,
    initial_prompt: str | None = None,
) -> tuple[list[Segment], dict[str, Any]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper is not installed. Run pip install -r scripts/requirements.txt") from exc

    started = time.perf_counter()
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    load_seconds = time.perf_counter() - started

    transcribe_started = time.perf_counter()
    raw_segments, info = model.transcribe(
        str(audio_path),
        language=language or None,
        beam_size=beam_size,
        vad_filter=vad_filter,
        initial_prompt=initial_prompt or None,
    )
    segments = [
        Segment(start=segment.start, end=segment.end, text=segment.text.strip())
        for segment in raw_segments
        if segment.text.strip()
    ]
    transcribe_seconds = time.perf_counter() - transcribe_started

    metadata = {
        "model": model_name,
        "device": device,
        "compute_type": compute_type,
        "language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "load_seconds": round(load_seconds, 3),
        "transcribe_seconds": round(transcribe_seconds, 3),
        "speed_ratio": round((getattr(info, "duration", 0.0) or 0.0) / transcribe_seconds, 3)
        if transcribe_seconds > 0
        else None,
        "segments": len(segments),
    }
    return segments, metadata


def segments_to_jsonable(segments: list[Segment]) -> list[dict[str, Any]]:
    return [asdict(segment) for segment in segments]
