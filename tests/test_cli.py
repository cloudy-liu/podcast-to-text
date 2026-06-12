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
            {"model": "tiny", "duration": 1.0, "segments": 1},
        ),
    )


def _run_cli(
    monkeypatch,
    tmp_path: Path,
    url: str = XIAOYUZHOU_URL,
    extra_args: list[str] | None = None,
) -> Path:
    out_dir = tmp_path / "out"
    argv = [
        "podcast-to-text",
        url,
        "--limit-seconds",
        "1",
        "--out-dir",
        str(out_dir),
    ]
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


def _stub_youtube_subtitle(monkeypatch, tmp_path: Path):
    calls = {"transcribe": 0}

    def fail_transcribe(*args, **kwargs):
        calls["transcribe"] += 1
        raise AssertionError("ASR should not run when YouTube platform subtitles are available")

    def fake_download_youtube_subtitle(source_url: str, output_dir: Path) -> YouTubeSubtitle:
        subtitle_path = output_dir / "platform.en.vtt"
        subtitle_path.write_text(
            "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nManual caption\n",
            encoding="utf-8",
        )
        return YouTubeSubtitle(
            video_id="dQw4w9WgXcQ",
            title="YouTube Demo: Video",
            source_url=source_url,
            webpage_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            subtitle_path=subtitle_path,
            language="en",
            subtitle_type="manual",
            duration=12.5,
            uploader="Example Channel",
        )

    monkeypatch.setattr(cli, "download_youtube_subtitle", fake_download_youtube_subtitle)
    monkeypatch.setattr(cli, "transcribe_audio", fail_transcribe)
    return calls


def test_cli_uses_readable_title_id_directory_by_default(monkeypatch, tmp_path):
    out_dir = _run_cli(monkeypatch, tmp_path)
    _stub_xiaoyuzhou(monkeypatch)

    assert cli.main() == 0

    assert (out_dir / "Episode Title- Harness__6a15a2cb").is_dir()


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


def test_cli_writes_srt_but_not_txt_for_xiaoyuzhou(monkeypatch, tmp_path):
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
    assert (video_dir / "segments.json").is_file()
    assert not (video_dir / "transcript.srt").exists()
    assert not (video_dir / "transcript.txt").exists()
    assert metadata["source_type"] == "youtube"
    assert metadata["video_id"] == "dQw4w9WgXcQ"


def test_cli_uses_youtube_platform_subtitle_without_asr(monkeypatch, tmp_path):
    out_dir = _run_cli(monkeypatch, tmp_path, url=YOUTUBE_URL)
    calls = _stub_youtube_subtitle(monkeypatch, tmp_path)

    assert cli.main() == 0

    video_dir = out_dir / "YouTube Demo- Video__dQw4w9Wg"
    metadata = json.loads((video_dir / "metadata.json").read_text(encoding="utf-8"))

    assert (video_dir / "source.srt").is_file()
    assert "Manual caption" in (video_dir / "source.srt").read_text(encoding="utf-8")
    assert calls["transcribe"] == 0
    assert metadata["source_type"] == "youtube"
    assert metadata["video_id"] == "dQw4w9WgXcQ"
