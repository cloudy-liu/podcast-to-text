from __future__ import annotations

import html as html_lib
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


EPISODE_PATH_RE = re.compile(r"^/episode/([0-9a-fA-F]{24})")
NEXT_DATA_RE = re.compile(
    r"<script[^>]*id=[\"']__NEXT_DATA__[\"'][^>]*>([\s\S]*?)</script>",
    re.IGNORECASE,
)
META_RE_TEMPLATE = r"<meta[^>]*property=[\"']{property_name}[\"'][^>]*content=[\"']([^\"']+)[\"'][^>]*>"


@dataclass(frozen=True)
class XiaoyuzhouTranscriptHint:
    media_id: str | None = None
    is_enabled: bool | None = None
    has_marker: bool = False
    public_fetch_available: bool = False
    source: str = "xiaoyuzhou_next_data"

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "media_id": self.media_id,
            "is_enabled": self.is_enabled,
            "has_marker": self.has_marker,
            "public_fetch_available": self.public_fetch_available,
        }


@dataclass(frozen=True)
class XiaoyuzhouEpisode:
    episode_id: str
    title: str
    audio_url: str
    source_url: str
    transcript_hint: XiaoyuzhouTranscriptHint = XiaoyuzhouTranscriptHint()


def is_xiaoyuzhou_episode_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and parsed.netloc in {
        "www.xiaoyuzhoufm.com",
        "xiaoyuzhoufm.com",
    } and bool(EPISODE_PATH_RE.match(parsed.path))


def resolve_xiaoyuzhou_from_html(source_url: str, page_html: str) -> XiaoyuzhouEpisode:
    if not is_xiaoyuzhou_episode_url(source_url):
        raise ValueError(f"Not a Xiaoyuzhou episode URL: {source_url}")

    next_episode = _extract_episode_from_next_data(page_html)
    og_audio = _extract_meta_property(page_html, "og:audio")
    og_title = _extract_meta_property(page_html, "og:title")

    audio_url = og_audio or _nested_string(next_episode, ("enclosure", "url"))
    audio_url = audio_url or _nested_string(next_episode, ("media", "source", "url"))
    if not audio_url:
        raise ValueError("Could not find Xiaoyuzhou episode audio URL.")

    episode_id = _string_value(next_episode.get("eid")) or _string_value(next_episode.get("id"))
    episode_id = episode_id or _episode_id_from_url(source_url)
    title = og_title or _string_value(next_episode.get("title")) or episode_id
    transcript_hint = _extract_transcript_hint(next_episode)

    return XiaoyuzhouEpisode(
        episode_id=episode_id,
        title=html_lib.unescape(title).strip(),
        audio_url=html_lib.unescape(audio_url).strip(),
        source_url=source_url,
        transcript_hint=transcript_hint,
    )


def _extract_meta_property(page_html: str, property_name: str) -> str | None:
    pattern = META_RE_TEMPLATE.format(property_name=re.escape(property_name))
    match = re.search(pattern, page_html, re.IGNORECASE)
    if match:
        return html_lib.unescape(match.group(1)).strip()
    return None


def _extract_episode_from_next_data(page_html: str) -> dict[str, Any]:
    match = NEXT_DATA_RE.search(page_html)
    if not match:
        return {}

    payload = html_lib.unescape(match.group(1)).strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return {}

    page_props = _as_dict(_as_dict(data.get("props")).get("pageProps"))
    direct_episode = _as_dict(page_props.get("episode"))
    if direct_episode:
        return direct_episode

    dehydrated_state = _as_dict(page_props.get("dehydratedState"))
    for query in _as_list(dehydrated_state.get("queries")):
        episode = _as_dict(_as_dict(_as_dict(query).get("state")).get("data")).get("episode")
        if isinstance(episode, dict):
            return episode

    return {}


def _episode_id_from_url(source_url: str) -> str:
    match = EPISODE_PATH_RE.match(urlparse(source_url).path)
    if not match:
        raise ValueError(f"Could not derive episode id from URL: {source_url}")
    return match.group(1)


def _nested_string(data: dict[str, Any], path: tuple[str, ...]) -> str | None:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return _string_value(current)


def _string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _extract_transcript_hint(episode: dict[str, Any]) -> XiaoyuzhouTranscriptHint:
    transcript = _as_dict(episode.get("transcript"))
    media_id = _string_value(episode.get("transcriptMediaId"))
    media_id = media_id or _string_value(transcript.get("mediaId"))
    is_enabled = _bool_value(episode.get("isTranscriptEnabled"))
    has_marker = bool(media_id or transcript)
    return XiaoyuzhouTranscriptHint(
        media_id=media_id,
        is_enabled=is_enabled,
        has_marker=has_marker,
        public_fetch_available=False,
    )


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
