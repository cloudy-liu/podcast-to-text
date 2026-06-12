from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


def render_srt(segments: list[Segment]) -> str:
    blocks = []
    for index, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if not text:
            continue
        blocks.append(
            f"{index}\n"
            f"{format_srt_timestamp(segment.start)} --> {format_srt_timestamp(segment.end)}\n"
            f"{text}\n"
        )
    return "\n".join(blocks) + ("\n" if blocks else "")


def format_srt_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def normalize_subtitle_to_srt(text: str) -> str:
    segments = parse_subtitle_segments(text)
    if segments:
        return render_srt(segments)

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized if normalized.endswith("\n") else normalized + "\n"


def parse_subtitle_segments(text: str) -> list[Segment]:
    lines = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = _skip_vtt_header(lines)
    segments: list[Segment] = []

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue

        if _is_vtt_metadata_block(line):
            index = _skip_until_blank(lines, index + 1)
            continue

        timestamp_line = line
        if "-->" not in timestamp_line:
            index += 1
            if index >= len(lines):
                break
            timestamp_line = lines[index].strip()

        timestamp_match = _TIMESTAMP_LINE_RE.match(timestamp_line)
        if not timestamp_match:
            index += 1
            continue

        start = _parse_subtitle_timestamp(timestamp_match.group("start"))
        end = _parse_subtitle_timestamp(timestamp_match.group("end"))
        index += 1

        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            cleaned = _clean_subtitle_text(lines[index].strip())
            if cleaned:
                text_lines.append(cleaned)
            index += 1

        cue_text = "\n".join(text_lines).strip()
        if cue_text:
            segments.append(Segment(start=start, end=end, text=cue_text))

    return segments


_TIMESTAMP_LINE_RE = re.compile(
    r"^(?P<start>(?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})\s+-->\s+"
    r"(?P<end>(?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})(?:\s+.*)?$"
)
_TAG_RE = re.compile(r"<[^>]+>")


def _skip_vtt_header(lines: list[str]) -> int:
    if not lines or not lines[0].lstrip().startswith("WEBVTT"):
        return 0

    index = 1
    while index < len(lines) and lines[index].strip():
        index += 1
    return index + 1


def _is_vtt_metadata_block(line: str) -> bool:
    return line == "STYLE" or line == "REGION" or line.startswith("NOTE")


def _skip_until_blank(lines: list[str], index: int) -> int:
    while index < len(lines) and lines[index].strip():
        index += 1
    return index


def _parse_subtitle_timestamp(value: str) -> float:
    timestamp, milliseconds = value.replace(",", ".").split(".")
    parts = [int(part) for part in timestamp.split(":")]
    if len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    else:
        hours, minutes, seconds = parts
    return hours * 3600 + minutes * 60 + seconds + int(milliseconds) / 1000


def _clean_subtitle_text(text: str) -> str:
    return unescape(_TAG_RE.sub("", text)).strip()
