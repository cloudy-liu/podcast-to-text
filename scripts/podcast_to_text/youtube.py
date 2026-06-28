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


@dataclass(frozen=True)
class _SubtitleSelection:
    language: str
    subtitle_type: str


CHINESE_SUBTITLE_LANGUAGES = ("zh-Hans", "zh-CN", "zh", "zh-Hant", "zh-TW")
ENGLISH_SUBTITLE_LANGUAGES = ("en", "en-US", "en-GB")
SUPPORTED_SUBTITLE_EXTENSIONS = {"vtt"}


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
    output_template = str(output_dir / "%(title).120s [%(id)s].%(ext)s")

    with YoutubeDL(_youtube_subtitle_probe_options()) as ydl:
        probe_info = ydl.extract_info(source_url, download=False)

    selection = _select_subtitle(probe_info)
    if selection is None:
        return None

    with YoutubeDL(_youtube_subtitle_download_options(output_template, selection)) as ydl:
        info = ydl.extract_info(source_url, download=True)

    video_id = str(info.get("id") or probe_info.get("id") or "")
    title = str(info.get("title") or probe_info.get("title") or video_id or "youtube-video")
    subtitle_path = _downloaded_subtitle_path(
        info=info,
        output_dir=output_dir,
        title=title,
        video_id=video_id,
        language=selection.language,
    )

    return YouTubeSubtitle(
        video_id=video_id,
        title=title,
        source_url=source_url,
        webpage_url=str(info.get("webpage_url") or probe_info.get("webpage_url") or source_url),
        subtitle_path=subtitle_path,
        language=selection.language,
        subtitle_type=selection.subtitle_type,
        duration=_float_or_none(info.get("duration") or probe_info.get("duration")),
        uploader=_string_or_none(
            info.get("uploader")
            or info.get("channel")
            or probe_info.get("uploader")
            or probe_info.get("channel")
        ),
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


def _youtube_subtitle_probe_options() -> dict[str, Any]:
    return {
        "skip_download": True,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
    }


def _youtube_subtitle_download_options(
    output_template: str, selection: _SubtitleSelection
) -> dict[str, Any]:
    return {
        "skip_download": True,
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        "writesubtitles": selection.subtitle_type == "manual",
        "writeautomaticsub": selection.subtitle_type == "automatic",
        "subtitleslangs": [selection.language],
        "subtitlesformat": "vtt",
    }


def _select_subtitle(info: dict[str, Any]) -> _SubtitleSelection | None:
    manual_subtitles = _as_dict(info.get("subtitles"))
    automatic_captions = _as_dict(info.get("automatic_captions"))

    for languages, subtitle_type, subtitles in (
        (CHINESE_SUBTITLE_LANGUAGES, "manual", manual_subtitles),
        (ENGLISH_SUBTITLE_LANGUAGES, "manual", manual_subtitles),
        (CHINESE_SUBTITLE_LANGUAGES, "automatic", automatic_captions),
        (ENGLISH_SUBTITLE_LANGUAGES, "automatic", automatic_captions),
    ):
        language = _find_supported_subtitle_language(subtitles, languages)
        if language is not None:
            return _SubtitleSelection(language=language, subtitle_type=subtitle_type)

    return None


def _find_supported_subtitle_language(
    subtitles: dict[str, Any], preferred_languages: tuple[str, ...]
) -> str | None:
    for language in preferred_languages:
        if _has_supported_subtitle(subtitles.get(language)):
            return language

    for language in subtitles:
        if language.startswith(preferred_languages) and _has_supported_subtitle(
            subtitles.get(language)
        ):
            return language

    return None


def _has_supported_subtitle(value: Any) -> bool:
    for subtitle in _as_list(value):
        if (
            isinstance(subtitle, dict)
            and subtitle.get("ext") in SUPPORTED_SUBTITLE_EXTENSIONS
        ):
            return True
    return False


def _downloaded_subtitle_path(
    *,
    info: dict[str, Any],
    output_dir: Path,
    title: str,
    video_id: str,
    language: str,
) -> Path:
    requested_subtitles = _as_dict(info.get("requested_subtitles"))
    for subtitle in requested_subtitles.values():
        if isinstance(subtitle, dict):
            filepath = subtitle.get("filepath")
            if isinstance(filepath, str) and filepath:
                return Path(filepath)

    for subtitle_path in output_dir.glob("*.vtt"):
        if (
            subtitle_path.name.endswith(f".{language}.vtt")
            and f"[{video_id}]" in subtitle_path.name
        ):
            return subtitle_path

    return output_dir / f"{title} [{video_id}].{language}.vtt"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None
