from __future__ import annotations

from dataclasses import dataclass


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


def render_vtt_as_srt(vtt_text: str) -> str:
    lines = vtt_text.replace("\ufeff", "").splitlines()
    blocks: list[str] = []
    index = 1
    cursor = 0

    while cursor < len(lines):
        line = lines[cursor].strip()
        if not line or line.startswith("WEBVTT"):
            cursor += 1
            continue

        if line.startswith(("NOTE", "STYLE", "REGION")):
            cursor = _skip_vtt_block(lines, cursor + 1)
            continue

        if "-->" in line:
            timing = line
            cursor += 1
        else:
            cursor += 1
            if cursor >= len(lines) or "-->" not in lines[cursor]:
                continue
            timing = lines[cursor].strip()
            cursor += 1

        start, end = _parse_vtt_timing(timing)
        text_lines: list[str] = []
        while cursor < len(lines) and lines[cursor].strip():
            text_lines.append(lines[cursor].strip())
            cursor += 1

        text = "\n".join(text_lines).strip()
        if text:
            blocks.append(
                f"{index}\n"
                f"{_format_vtt_timestamp(start)} --> {_format_vtt_timestamp(end)}\n"
                f"{text}\n"
            )
            index += 1

    return "\n".join(blocks) + ("\n" if blocks else "")


def format_srt_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _skip_vtt_block(lines: list[str], cursor: int) -> int:
    while cursor < len(lines) and lines[cursor].strip():
        cursor += 1
    return cursor


def _parse_vtt_timing(timing: str) -> tuple[str, str]:
    start, rest = timing.split("-->", maxsplit=1)
    end = rest.strip().split()[0]
    return start.strip(), end.strip()


def _format_vtt_timestamp(timestamp: str) -> str:
    return timestamp.replace(".", ",", 1)
