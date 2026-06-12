from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL


YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}


@dataclass(frozen=True)
class YouTubeVideo:
    video_id: str
    title: str
    source_url: str
    webpage_url: str
    audio_path: Path
    duration: float | None = None
    uploader: str | None = None


def is_youtube_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    host = parsed.netloc.lower()
    if host == "youtu.be":
        return bool(parsed.path.strip("/"))

    if host not in YOUTUBE_HOSTS:
        return False

    if parsed.path == "/watch":
        return bool(parse_qs(parsed.query).get("v"))

    return parsed.path.startswith(("/shorts/", "/live/"))


def download_youtube_audio(source_url: str, output_dir: Path) -> YouTubeVideo:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(title).120s [%(id)s].%(ext)s")
    options: dict[str, Any] = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(source_url, download=True)

    audio_path = _downloaded_audio_path(info)
    return YouTubeVideo(
        video_id=str(info.get("id") or ""),
        title=str(info.get("title") or info.get("id") or "youtube-video"),
        source_url=source_url,
        webpage_url=str(info.get("webpage_url") or source_url),
        audio_path=audio_path,
        duration=_float_or_none(info.get("duration")),
        uploader=_string_or_none(info.get("uploader") or info.get("channel")),
    )


def _downloaded_audio_path(info: dict[str, Any]) -> Path:
    for download in _as_list(info.get("requested_downloads")):
        if isinstance(download, dict):
            filepath = download.get("filepath")
            if isinstance(filepath, str) and filepath:
                return Path(filepath)

    requested_filename = info.get("requested_filename")
    if isinstance(requested_filename, str) and requested_filename:
        return Path(requested_filename)

    raise RuntimeError("yt-dlp did not report a downloaded audio file path.")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None
