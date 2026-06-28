from __future__ import annotations

import re
from typing import Any


MAX_CALIBRATION_PROMPT_CHARS = 900


def build_asr_calibration_prompt(
    metadata: dict[str, Any],
    user_prompt: str | None = None,
) -> str | None:
    lines: list[str] = []

    cleaned_user_prompt = _clean(user_prompt)
    if cleaned_user_prompt:
        lines.append(f"User hint: {cleaned_user_prompt}")

    source_type = _clean(metadata.get("source_type"))
    if source_type:
        lines.append(f"Source type: {source_type}")

    title = _clean(metadata.get("title"))
    if title:
        lines.append(f"Title: {title}")

    uploader = _clean(metadata.get("uploader"))
    if uploader:
        lines.append(f"Channel: {uploader}")

    source_id = _clean(metadata.get("episode_id") or metadata.get("video_id"))
    if source_id:
        lines.append(f"Source id: {source_id}")

    if not lines:
        return None

    prompt = "\n".join(lines)
    return prompt[:MAX_CALIBRATION_PROMPT_CHARS].rstrip()


def describe_transcription_calibration(prompt: str) -> dict[str, object]:
    return {
        "artifact": "metadata.json",
        "method": "source_metadata_prompt",
        "used_for_asr": True,
        "prompt": prompt,
    }


def _clean(value: object) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned or None
