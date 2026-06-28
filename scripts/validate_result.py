from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


AUDIO_SUFFIXES = {".m4a", ".mp3", ".mp4", ".wav", ".webm"}
FORBIDDEN_NAMES = {"segments.json", "transcript.srt"}
FORBIDDEN_DIR_NAMES = {".youtube-downloads", "chunks", "chunk", "tmp", "temp"}
CJK_RE = re.compile(r"[\u3400-\u9fff]")
SRT_BLOCK_RE = re.compile(
    r"(?ms)^\s*\d+\s*\n"
    r"\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}\s*\n"
    r".+?(?=\n\s*\n|\Z)"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate lightweight podcast-to-text result artifacts."
    )
    parser.add_argument(
        "result_dir",
        nargs="?",
        default="output/result",
        type=Path,
        help="Result root or a single result item directory.",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Allow source-only partial results without transcript.zh.srt.",
    )
    args = parser.parse_args()

    errors = validate(args.result_dir, allow_partial=args.allow_partial)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.result_dir}")
    return 0


def validate(path: Path, *, allow_partial: bool) -> list[str]:
    errors: list[str] = []
    root = path.resolve()
    if not root.exists():
        return [f"{path} does not exist"]

    errors.extend(_find_forbidden_files(root))
    item_dirs = _result_item_dirs(root)
    if not item_dirs:
        errors.append(f"{path} has no result item directories")
        return errors

    for item_dir in item_dirs:
        errors.extend(_validate_item(item_dir, allow_partial=allow_partial))

    return errors


def _result_item_dirs(root: Path) -> list[Path]:
    if (root / "metadata.json").exists():
        return [root]

    return sorted(
        child
        for child in root.iterdir()
        if child.is_dir() and not child.name.startswith(".")
    )


def _find_forbidden_files(root: Path) -> list[str]:
    errors: list[str] = []
    for item in root.rglob("*"):
        if item.is_dir() and item.name.lower() in FORBIDDEN_DIR_NAMES:
            errors.append(f"forbidden directory in result: {item}")
        if not item.is_file():
            continue
        if item.suffix.lower() in AUDIO_SUFFIXES:
            errors.append(f"audio/video file must not remain in result: {item}")
        if item.name in FORBIDDEN_NAMES:
            errors.append(f"forbidden legacy/intermediate file in result: {item}")
    return errors


def _validate_item(item_dir: Path, *, allow_partial: bool) -> list[str]:
    errors: list[str] = []
    metadata = item_dir / "metadata.json"
    transcript = item_dir / "transcript.zh.srt"
    insights = item_dir / "insights.md"
    source = item_dir / "source.srt"

    if not metadata.exists():
        errors.append(f"missing metadata.json: {item_dir}")
    if not insights.exists():
        errors.append(f"missing insights.md: {item_dir}")

    has_transcript = transcript.exists()
    has_source = source.exists()
    if not has_transcript:
        if allow_partial and has_source:
            pass
        else:
            errors.append(f"missing transcript.zh.srt: {item_dir}")

    if has_transcript:
        errors.extend(_validate_srt(transcript, require_cjk=True))
    if has_source:
        errors.extend(_validate_srt(source, require_cjk=False))
    if insights.exists():
        errors.extend(_validate_text_has_cjk(insights, "insights.md must be Chinese"))

    return errors


def _validate_srt(path: Path, *, require_cjk: bool) -> list[str]:
    errors: list[str] = []
    text = _read_text(path, errors)
    if text is None:
        return errors
    if not text.strip():
        errors.append(f"empty SRT file: {path}")
        return errors
    if not SRT_BLOCK_RE.search(text):
        errors.append(f"file does not look like SRT: {path}")
    if require_cjk and not CJK_RE.search(text):
        errors.append(f"transcript.zh.srt must contain Chinese text: {path}")
    return errors


def _validate_text_has_cjk(path: Path, message: str) -> list[str]:
    errors: list[str] = []
    text = _read_text(path, errors)
    if text is None:
        return errors
    if not text.strip():
        errors.append(f"empty file: {path}")
    elif not CJK_RE.search(text):
        errors.append(f"{message}: {path}")
    return errors


def _read_text(path: Path, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        errors.append(f"file is not valid UTF-8: {path} ({exc})")
        return None


if __name__ == "__main__":
    raise SystemExit(main())
