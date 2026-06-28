from __future__ import annotations

import sys
import types
from pathlib import Path

from podcast_to_text.transcriber import transcribe_audio


class _FakeSegment:
    start = 0.0
    end = 1.0
    text = " 你好 "


class _FakeInfo:
    language = "zh"
    language_probability = 1.0
    duration = 1.0


def test_passes_initial_prompt_to_faster_whisper(monkeypatch):
    captured = {}

    class FakeWhisperModel:
        def __init__(self, model_name, *, device, compute_type):
            captured["init"] = {
                "model_name": model_name,
                "device": device,
                "compute_type": compute_type,
            }

        def transcribe(self, audio_path, **kwargs):
            captured["audio_path"] = audio_path
            captured["kwargs"] = kwargs
            return [_FakeSegment()], _FakeInfo()

    fake_module = types.SimpleNamespace(WhisperModel=FakeWhisperModel)
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_module)

    segments, metadata = transcribe_audio(
        Path("sample.wav"),
        model_name="medium",
        device="cpu",
        compute_type="int8",
        language="zh",
        beam_size=5,
        vad_filter=False,
        initial_prompt="Sheet0, 王文锋, AI Agent, Manus",
    )

    assert captured["init"] == {
        "model_name": "medium",
        "device": "cpu",
        "compute_type": "int8",
    }
    assert captured["audio_path"] == "sample.wav"
    assert captured["kwargs"]["initial_prompt"] == "Sheet0, 王文锋, AI Agent, Manus"
    assert segments[0].text == "你好"
    assert metadata["segments"] == 1
