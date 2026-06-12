from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CueSignature:
    index: str
    start: str
    end: str


TIMESTAMP_LINE_RE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2},\d{3})(?:\s+.*)?$"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate that transcript.zh.srt preserves source.srt cue alignment."
    )
    parser.add_argument("source_srt", type=Path)
    parser.add_argument("target_srt", type=Path)
    args = parser.parse_args()

    source = parse_srt_signatures(args.source_srt)
    target = parse_srt_signatures(args.target_srt)

    error = compare_signatures(source, target)
    if error:
        print(error, file=sys.stderr)
        return 1

    print(f"OK: {len(source)} cues aligned")
    return 0


def parse_srt_signatures(path: Path) -> list[CueSignature]:
    text = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n").strip())
    signatures: list[CueSignature] = []

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue

        index = lines[0]
        timestamp_line = lines[1]
        match = TIMESTAMP_LINE_RE.match(timestamp_line)
        if not match:
            raise ValueError(f"{path}: invalid timestamp line after cue {index!r}")

        signatures.append(
            CueSignature(
                index=index,
                start=match.group("start"),
                end=match.group("end"),
            )
        )

    return signatures


def compare_signatures(source: list[CueSignature], target: list[CueSignature]) -> str | None:
    if len(source) != len(target):
        return f"cue count mismatch: source={len(source)} target={len(target)}"

    for position, (source_cue, target_cue) in enumerate(zip(source, target), start=1):
        if source_cue.index != target_cue.index:
            return (
                f"cue index mismatch at position {position}: "
                f"source={source_cue.index} target={target_cue.index}"
            )

        if source_cue.start != target_cue.start or source_cue.end != target_cue.end:
            return (
                f"timestamp mismatch at cue {source_cue.index}: "
                f"source={source_cue.start} --> {source_cue.end} "
                f"target={target_cue.start} --> {target_cue.end}"
            )

    return None


if __name__ == "__main__":
    raise SystemExit(main())
