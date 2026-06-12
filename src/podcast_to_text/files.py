from __future__ import annotations

import re


def safe_name(value: str, fallback: str = "episode", max_length: int = 120) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\uff1a\x00-\x1f]+', "-", value).strip(" .-")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned[:max_length].strip(" .-")
    return cleaned or fallback


def episode_directory_name(
    *,
    title: str,
    episode_id: str,
    template: str = "title-id",
    max_length: int = 120,
) -> str:
    if template == "id":
        return safe_name(episode_id, fallback="episode", max_length=max_length)

    if template == "title":
        return safe_name(title, fallback=episode_id or "episode", max_length=max_length)

    if template != "title-id":
        raise ValueError(f"Unsupported directory template: {template}")

    short_id = safe_name(episode_id, fallback="episode", max_length=8)
    suffix = f"__{short_id}"
    title_length = max(max_length - len(suffix), 1)
    title_part = safe_name(title, fallback=episode_id or "episode", max_length=title_length)
    return f"{title_part}{suffix}"
