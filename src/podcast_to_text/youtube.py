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


@dataclass(frozen=True)
class YouTubeSubtitle:
    video_id: str
    title: str
    source_url: str
    webpage_url: str
    subtitle_path: Path
    language: str
    subtitle_type: str
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


def download_youtube_subtitle(source_url: str, output_dir: Path) -> YouTubeSubtitle | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    probe_options: dict[str, Any] = {
        "skip_download": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with YoutubeDL(probe_options) as ydl:
        info = ydl.extract_info(source_url, download=False)

    selected = _select_subtitle(info)
    if selected is None:
        return None

    language, subtitle_type = selected
    output_template = str(output_dir / "%(title).120s [%(id)s].%(ext)s")
    download_options: dict[str, Any] = {
        "skip_download": True,
        "writesubtitles": subtitle_type == "manual",
        "writeautomaticsub": subtitle_type == "automatic",
        "subtitleslangs": [language],
        "subtitlesformat": "srt/vtt/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
    }

    with YoutubeDL(download_options) as ydl:
        downloaded_info = ydl.extract_info(source_url, download=True)

    subtitle_path = _downloaded_subtitle_path(downloaded_info, output_dir, language)
    metadata = downloaded_info if isinstance(downloaded_info, dict) else info
    return YouTubeSubtitle(
        video_id=str(metadata.get("id") or ""),
        title=str(metadata.get("title") or metadata.get("id") or "youtube-video"),
        source_url=source_url,
        webpage_url=str(metadata.get("webpage_url") or source_url),
        subtitle_path=subtitle_path,
        language=language,
        subtitle_type=subtitle_type,
        duration=_float_or_none(metadata.get("duration")),
        uploader=_string_or_none(metadata.get("uploader") or metadata.get("channel")),
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


def _select_subtitle(info: dict[str, Any]) -> tuple[str, str] | None:
    manual_subtitles = _as_dict(info.get("subtitles"))
    automatic_subtitles = _as_dict(info.get("automatic_captions"))

    for captions, subtitle_type, language_family in (
        (manual_subtitles, "manual", "zh"),
        (manual_subtitles, "manual", "en"),
        (automatic_subtitles, "automatic", "zh"),
        (automatic_subtitles, "automatic", "en"),
    ):
        language = _select_language(captions, language_family)
        if language:
            return language, subtitle_type

    return None


def _select_language(captions: dict[str, Any], language_family: str) -> str | None:
    preferred = (
        _CHINESE_LANGUAGE_PRIORITY
        if language_family == "zh"
        else _ENGLISH_LANGUAGE_PRIORITY
    )
    available = [
        language for language in captions if _has_downloadable_caption(captions[language])
    ]

    for language in preferred:
        if language in available:
            return language

    matching = sorted(
        language for language in available if _language_matches(language, language_family)
    )
    return matching[0] if matching else None


def _has_downloadable_caption(entries: Any) -> bool:
    if not isinstance(entries, list):
        return False
    if not entries:
        return False
    return any(
        not isinstance(entry, dict) or entry.get("ext") in {None, "srt", "vtt"}
        for entry in entries
    )


def _language_matches(language: str, language_family: str) -> bool:
    normalized = language.lower()
    if language_family == "zh":
        return normalized == "zh" or normalized.startswith("zh-")
    return normalized == "en" or normalized.startswith("en-")


def _downloaded_subtitle_path(info: dict[str, Any], output_dir: Path, language: str) -> Path:
    requested_subtitles = _as_dict(info.get("requested_subtitles"))
    subtitle_info = _as_dict(requested_subtitles.get(language))
    for key in ("filepath", "filename"):
        filepath = subtitle_info.get(key)
        if isinstance(filepath, str) and filepath:
            return Path(filepath)

    matching_paths = sorted(
        path
        for path in output_dir.iterdir()
        if path.is_file() and f".{language}." in path.name
    )
    if matching_paths:
        return matching_paths[-1]

    raise RuntimeError("yt-dlp did not report a downloaded subtitle file path.")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


_CHINESE_LANGUAGE_PRIORITY = (
    "zh-Hans",
    "zh-CN",
    "zh",
    "zh-Hant",
    "zh-TW",
    "zh-HK",
)
_ENGLISH_LANGUAGE_PRIORITY = ("en", "en-US", "en-GB")
