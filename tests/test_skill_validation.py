from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "chinese-srt-adaptation"
    / "scripts"
    / "validate_srt_alignment.py"
)


def test_validate_srt_alignment_accepts_matching_cues(tmp_path):
    source = tmp_path / "source.srt"
    target = tmp_path / "transcript.zh.srt"
    source.write_text(_srt_text("00:00:00,000", "00:00:01,000", "hello"), encoding="utf-8")
    target.write_text(_srt_text("00:00:00,000", "00:00:01,000", "你好"), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(source), str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "OK" in result.stdout


def test_validate_srt_alignment_rejects_changed_timestamps(tmp_path):
    source = tmp_path / "source.srt"
    target = tmp_path / "transcript.zh.srt"
    source.write_text(_srt_text("00:00:00,000", "00:00:01,000", "hello"), encoding="utf-8")
    target.write_text(_srt_text("00:00:00,250", "00:00:01,000", "你好"), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(source), str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "timestamp mismatch" in result.stderr


def _srt_text(start: str, end: str, text: str) -> str:
    return f"1\n{start} --> {end}\n{text}\n"
