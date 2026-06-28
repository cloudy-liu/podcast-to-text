from __future__ import annotations

import json
from pathlib import Path

from podcast_to_text import cli
from podcast_to_text.outputs import Segment
from podcast_to_text.xiaoyuzhou import XiaoyuzhouEpisode, XiaoyuzhouTranscriptHint
from podcast_to_text.youtube import YouTubeSubtitle, YouTubeVideo


XIAOYUZHOU_URL = "https://www.xiaoyuzhoufm.com/episode/6a15a2cbff7b9a8c0a5b953f"
YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def _stub_transcriber(monkeypatch):
    monkeypatch.setattr(
        cli,
        "transcribe_audio",
        lambda *args, **kwargs: (
            [Segment(start=0.0, end=1.0, text="hello world")],
            {"model": "tiny", "duration": 1.0, "segments": 1, "language": "en"},
        ),
    )


def _run_cli(
    monkeypatch,
    tmp_path: Path,
    url: str = XIAOYUZHOU_URL,
    extra_args: list[str] | None = None,
    include_out_dir: bool = True,
) -> Path:
    out_dir = tmp_path / "out"
    argv = [
        "podcast-to-text",
        url,
        "--limit-seconds",
        "1",
    ]
    if include_out_dir:
        argv.extend(["--out-dir", str(out_dir)])
    argv.extend(extra_args or [])

    monkeypatch.setattr("sys.argv", argv)
    _stub_transcriber(monkeypatch)
    return out_dir


def _stub_xiaoyuzhou(monkeypatch):
    monkeypatch.setattr(cli, "fetch_text", lambda url: "<html></html>")
    monkeypatch.setattr(
        cli,
        "resolve_xiaoyuzhou_from_html",
        lambda source_url, page_html: XiaoyuzhouEpisode(
            episode_id="6a15a2cbff7b9a8c0a5b953f",
            title="Episode Title: Harness",
            audio_url="https://media.xyzcdn.net/example/audio.m4a",
            source_url=source_url,
            transcript_hint=XiaoyuzhouTranscriptHint(
                media_id="example/audio.m4a",
                is_enabled=True,
                has_marker=True,
                public_fetch_available=False,
            ),
        ),
    )
    monkeypatch.setattr(
        cli,
        "extract_audio_sample",
        lambda audio_url, output_path, seconds: Path(output_path).write_bytes(b"wav"),
    )


def _stub_youtube(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cli, "download_youtube_subtitle", lambda source_url, output_dir: None)

    def fake_download_youtube_audio(source_url: str, output_dir: Path) -> YouTubeVideo:
        audio_path = output_dir / "youtube-audio.m4a"
        audio_path.write_bytes(b"audio")
        return YouTubeVideo(
            video_id="dQw4w9WgXcQ",
            title="YouTube Demo: Video",
            source_url=source_url,
            webpage_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            audio_path=audio_path,
            duration=12.5,
            uploader="Example Channel",
        )

    monkeypatch.setattr(cli, "download_youtube_audio", fake_download_youtube_audio)
    monkeypatch.setattr(
        cli,
        "extract_audio_sample",
        lambda audio_url, output_path, seconds: Path(output_path).write_bytes(b"wav"),
    )


def test_cli_uses_readable_title_id_directory_by_default(monkeypatch, tmp_path):
    out_dir = _run_cli(monkeypatch, tmp_path)
    _stub_xiaoyuzhou(monkeypatch)

    assert cli.main() == 0

    assert (out_dir / "Episode Title- Harness__6a15a2cb").is_dir()


def test_cli_uses_output_directory_when_out_dir_is_omitted(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    default_output_dir = tmp_path / "skill-output"
    monkeypatch.setattr(cli, "DEFAULT_OUTPUT_DIR", default_output_dir)
    _run_cli(monkeypatch, tmp_path, include_out_dir=False)
    _stub_xiaoyuzhou(monkeypatch)

    assert cli.main() == 0

    assert (default_output_dir / "Episode Title- Harness__6a15a2cb").is_dir()


def test_cli_can_use_legacy_episode_id_directory(monkeypatch, tmp_path):
    out_dir = _run_cli(monkeypatch, tmp_path, extra_args=["--dir-template", "id"])
    _stub_xiaoyuzhou(monkeypatch)

    assert cli.main() == 0

    assert (out_dir / "6a15a2cbff7b9a8c0a5b953f").is_dir()


def test_cli_writes_platform_transcript_hint_to_metadata(monkeypatch, tmp_path):
    out_dir = _run_cli(monkeypatch, tmp_path)
    _stub_xiaoyuzhou(monkeypatch)

    assert cli.main() == 0

    metadata_path = out_dir / "Episode Title- Harness__6a15a2cb" / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert metadata["platform_transcript_hint"] == {
        "source": "xiaoyuzhou_next_data",
        "media_id": "example/audio.m4a",
        "is_enabled": True,
        "has_marker": True,
        "public_fetch_available": False,
    }


def test_cli_passes_source_metadata_as_asr_calibration_prompt(monkeypatch, tmp_path):
    out_dir = _run_cli(monkeypatch, tmp_path)
    _stub_xiaoyuzhou(monkeypatch)
    captured = {}

    def fake_transcribe_audio(audio_path, **kwargs):
        captured.update(kwargs)
        return (
            [Segment(start=0.0, end=1.0, text="hello world")],
            {"model": "tiny", "duration": 1.0, "segments": 1, "language": "en"},
        )

    monkeypatch.setattr(cli, "transcribe_audio", fake_transcribe_audio)

    assert cli.main() == 0

    prompt = captured["initial_prompt"]
    assert "Source type: xiaoyuzhou" in prompt
    assert "Title: Episode Title: Harness" in prompt
    assert "Source id: 6a15a2cbff7b9a8c0a5b953f" in prompt

    metadata_path = out_dir / "Episode Title- Harness__6a15a2cb" / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["transcription_calibration"] == {
        "artifact": "metadata.json",
        "method": "source_metadata_prompt",
        "used_for_asr": True,
        "prompt": prompt,
    }


def test_cli_combines_user_prompt_with_source_metadata_calibration(monkeypatch, tmp_path):
    _run_cli(
        monkeypatch,
        tmp_path,
        extra_args=["--initial-prompt", "User terms: Harness, Stanley Druckenmiller"],
    )
    _stub_xiaoyuzhou(monkeypatch)
    captured = {}

    def fake_transcribe_audio(audio_path, **kwargs):
        captured.update(kwargs)
        return (
            [Segment(start=0.0, end=1.0, text="hello world")],
            {"model": "tiny", "duration": 1.0, "segments": 1, "language": "en"},
        )

    monkeypatch.setattr(cli, "transcribe_audio", fake_transcribe_audio)

    assert cli.main() == 0

    prompt = captured["initial_prompt"]
    assert prompt.startswith("User hint: User terms: Harness, Stanley Druckenmiller")
    assert "Title: Episode Title: Harness" in prompt


def test_cli_writes_source_srt_but_not_legacy_transcript_for_xiaoyuzhou(monkeypatch, tmp_path):
    out_dir = _run_cli(monkeypatch, tmp_path)
    _stub_xiaoyuzhou(monkeypatch)

    assert cli.main() == 0

    episode_dir = out_dir / "Episode Title- Harness__6a15a2cb"
    assert (episode_dir / "source.srt").is_file()
    assert not (episode_dir / "transcript.srt").exists()
    assert not (episode_dir / "transcript.txt").exists()


def test_cli_supports_youtube_urls(monkeypatch, tmp_path):
    out_dir = _run_cli(monkeypatch, tmp_path, url=YOUTUBE_URL)
    _stub_youtube(monkeypatch, tmp_path)

    assert cli.main() == 0

    video_dir = out_dir / "YouTube Demo- Video__dQw4w9Wg"
    metadata = json.loads((video_dir / "metadata.json").read_text(encoding="utf-8"))

    assert video_dir.is_dir()
    assert (video_dir / "source.srt").is_file()
    assert not (video_dir / "transcript.srt").exists()
    assert (video_dir / "segments.json").is_file()
    assert not (video_dir / "transcript.txt").exists()
    assert metadata["source_type"] == "youtube"
    assert metadata["video_id"] == "dQw4w9WgXcQ"
    assert metadata["source_transcript"] == {
        "artifact": "source.srt",
        "method": "local_asr",
        "provider": "faster-whisper",
        "asr_used": True,
        "language": "en",
    }
    assert metadata["transcription_calibration"]["used_for_asr"] is True
    assert "Title: YouTube Demo: Video" in metadata["transcription_calibration"]["prompt"]
    assert "Channel: Example Channel" in metadata["transcription_calibration"]["prompt"]


def test_cli_uses_youtube_platform_subtitle_before_asr(monkeypatch, tmp_path):
    out_dir = tmp_path / "out"
    subtitle_path = tmp_path / "caption.en.vtt"
    subtitle_path.write_text(
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:01.250\n"
        "Manual caption\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "podcast-to-text",
            YOUTUBE_URL,
            "--out-dir",
            str(out_dir),
        ],
    )
    monkeypatch.setattr(
        cli,
        "download_youtube_subtitle",
        lambda source_url, output_dir: YouTubeSubtitle(
            video_id="dQw4w9WgXcQ",
            title="YouTube Demo: Video",
            source_url=source_url,
            webpage_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            subtitle_path=subtitle_path,
            language="en",
            subtitle_type="manual",
            duration=12.5,
            uploader="Example Channel",
        ),
    )
    monkeypatch.setattr(
        cli,
        "download_youtube_audio",
        lambda source_url, output_dir: (_ for _ in ()).throw(
            AssertionError("audio download should not run when platform subtitles exist")
        ),
    )
    monkeypatch.setattr(
        cli,
        "transcribe_audio",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("ASR should not run when platform subtitles exist")
        ),
    )

    assert cli.main() == 0

    video_dir = out_dir / "YouTube Demo- Video__dQw4w9Wg"
    metadata = json.loads((video_dir / "metadata.json").read_text(encoding="utf-8"))

    assert (video_dir / "source.srt").read_text(encoding="utf-8") == (
        "1\n"
        "00:00:00,000 --> 00:00:01,250\n"
        "Manual caption\n\n"
    )
    assert not (video_dir / "transcript.srt").exists()
    assert not (video_dir / "segments.json").exists()
    assert metadata["source_transcript"] == {
        "artifact": "source.srt",
        "method": "platform_subtitle",
        "provider": "youtube",
        "asr_used": False,
        "language": "en",
        "subtitle_type": "manual",
    }
