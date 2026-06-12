from __future__ import annotations

from pathlib import Path
from typing import Any

from podcast_to_text.youtube import (
    YouTubeSubtitle,
    YouTubeVideo,
    download_youtube_audio,
    download_youtube_subtitle,
    is_youtube_url,
)


def test_recognizes_youtube_urls():
    assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ")
    assert is_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")
    assert is_youtube_url("https://www.youtube.com/live/dQw4w9WgXcQ")
    assert not is_youtube_url(
        "https://www.xiaoyuzhoufm.com/episode/6a15a2cbff7b9a8c0a5b953f"
    )


def test_download_youtube_audio_uses_yt_dlp(monkeypatch, tmp_path):
    calls = []

    class FakeYoutubeDL:
        def __init__(self, options):
            calls.append(("init", options))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def extract_info(self, url, download):
            calls.append(("extract_info", url, download))
            audio_path = tmp_path / "video audio [abc123].m4a"
            audio_path.write_bytes(b"audio")
            return {
                "id": "abc123",
                "title": "video audio",
                "webpage_url": "https://www.youtube.com/watch?v=abc123",
                "duration": 12.5,
                "uploader": "Example Channel",
                "requested_downloads": [{"filepath": str(audio_path)}],
            }

    monkeypatch.setattr("podcast_to_text.youtube.YoutubeDL", FakeYoutubeDL)

    video = download_youtube_audio("https://youtu.be/abc123", tmp_path)

    assert video == YouTubeVideo(
        video_id="abc123",
        title="video audio",
        source_url="https://youtu.be/abc123",
        webpage_url="https://www.youtube.com/watch?v=abc123",
        audio_path=tmp_path / "video audio [abc123].m4a",
        duration=12.5,
        uploader="Example Channel",
    )
    assert calls[1] == ("extract_info", "https://youtu.be/abc123", True)


def test_download_youtube_subtitle_prefers_manual_chinese(monkeypatch, tmp_path):
    info = {
        "id": "abc123",
        "title": "video audio",
        "webpage_url": "https://www.youtube.com/watch?v=abc123",
        "duration": 12.5,
        "uploader": "Example Channel",
        "subtitles": {
            "en": [{"ext": "vtt", "url": "https://example.test/manual-en.vtt"}],
            "zh-Hans": [{"ext": "vtt", "url": "https://example.test/manual-zh.vtt"}],
        },
        "automatic_captions": {
            "zh-Hans": [{"ext": "vtt", "url": "https://example.test/auto-zh.vtt"}]
        },
    }
    calls = _stub_subtitle_downloader(monkeypatch, tmp_path, info)

    subtitle = download_youtube_subtitle("https://youtu.be/abc123", tmp_path)

    assert subtitle == YouTubeSubtitle(
        video_id="abc123",
        title="video audio",
        source_url="https://youtu.be/abc123",
        webpage_url="https://www.youtube.com/watch?v=abc123",
        subtitle_path=tmp_path / "video audio [abc123].zh-Hans.vtt",
        language="zh-Hans",
        subtitle_type="manual",
        duration=12.5,
        uploader="Example Channel",
    )
    download_options = calls[2][1]
    assert download_options["skip_download"] is True
    assert download_options["writesubtitles"] is True
    assert download_options["writeautomaticsub"] is False
    assert download_options["subtitleslangs"] == ["zh-Hans"]
    assert calls[1] == ("extract_info", "https://youtu.be/abc123", False)
    assert calls[3] == ("extract_info", "https://youtu.be/abc123", True)


def test_download_youtube_subtitle_prefers_manual_english_over_auto_chinese(
    monkeypatch, tmp_path
):
    info = {
        "id": "abc123",
        "title": "video audio",
        "webpage_url": "https://www.youtube.com/watch?v=abc123",
        "subtitles": {
            "en": [{"ext": "vtt", "url": "https://example.test/manual-en.vtt"}],
        },
        "automatic_captions": {
            "zh-Hans": [{"ext": "vtt", "url": "https://example.test/auto-zh.vtt"}]
        },
    }
    calls = _stub_subtitle_downloader(monkeypatch, tmp_path, info)

    subtitle = download_youtube_subtitle("https://youtu.be/abc123", tmp_path)

    assert subtitle is not None
    assert subtitle.subtitle_type == "manual"
    assert subtitle.language == "en"
    assert calls[2][1]["writesubtitles"] is True
    assert calls[2][1]["writeautomaticsub"] is False
    assert calls[2][1]["subtitleslangs"] == ["en"]


def test_download_youtube_subtitle_tries_next_candidate_after_download_failure(
    monkeypatch, tmp_path
):
    info = {
        "id": "abc123",
        "title": "video audio",
        "webpage_url": "https://www.youtube.com/watch?v=abc123",
        "subtitles": {
            "zh-Hans": [{"ext": "vtt", "url": "https://example.test/manual-zh.vtt"}],
            "en": [{"ext": "vtt", "url": "https://example.test/manual-en.vtt"}],
        },
    }
    calls = _stub_subtitle_downloader(
        monkeypatch,
        tmp_path,
        info,
        fail_languages={"zh-Hans"},
    )

    subtitle = download_youtube_subtitle("https://youtu.be/abc123", tmp_path)

    assert subtitle is not None
    assert subtitle.language == "en"
    assert calls[2][1]["subtitleslangs"] == ["zh-Hans"]
    assert calls[4][1]["subtitleslangs"] == ["en"]


def test_download_youtube_subtitle_uses_auto_chinese_before_auto_english(
    monkeypatch, tmp_path
):
    info = {
        "id": "abc123",
        "title": "video audio",
        "webpage_url": "https://www.youtube.com/watch?v=abc123",
        "automatic_captions": {
            "en": [{"ext": "vtt", "url": "https://example.test/auto-en.vtt"}],
            "zh-Hans": [{"ext": "vtt", "url": "https://example.test/auto-zh.vtt"}],
        },
    }
    calls = _stub_subtitle_downloader(monkeypatch, tmp_path, info)

    subtitle = download_youtube_subtitle("https://youtu.be/abc123", tmp_path)

    assert subtitle is not None
    assert subtitle.subtitle_type == "automatic"
    assert subtitle.language == "zh-Hans"
    assert calls[2][1]["writesubtitles"] is False
    assert calls[2][1]["writeautomaticsub"] is True
    assert calls[2][1]["subtitleslangs"] == ["zh-Hans"]


def test_download_youtube_subtitle_returns_none_when_no_supported_subtitles(
    monkeypatch, tmp_path
):
    calls = []

    class FakeYoutubeDL:
        def __init__(self, options):
            calls.append(("init", options))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def extract_info(self, url, download):
            calls.append(("extract_info", url, download))
            return {
                "id": "abc123",
                "title": "video audio",
                "webpage_url": "https://www.youtube.com/watch?v=abc123",
                "subtitles": {},
                "automatic_captions": {},
            }

    monkeypatch.setattr("podcast_to_text.youtube.YoutubeDL", FakeYoutubeDL)

    assert download_youtube_subtitle("https://youtu.be/abc123", tmp_path) is None
    assert len(calls) == 2
    assert calls[1] == ("extract_info", "https://youtu.be/abc123", False)


def _stub_subtitle_downloader(
    monkeypatch,
    tmp_path: Path,
    info: dict[str, Any],
    fail_languages: set[str] | None = None,
) -> list[tuple[Any, ...]]:
    calls: list[tuple[Any, ...]] = []
    fail_languages = fail_languages or set()

    class FakeYoutubeDL:
        def __init__(self, options):
            self.options = options
            calls.append(("init", options))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def extract_info(self, url, download):
            calls.append(("extract_info", url, download))
            if not download:
                return info

            language = self.options["subtitleslangs"][0]
            if language in fail_languages:
                raise RuntimeError(f"download failed for {language}")

            subtitle_path = tmp_path / f"video audio [abc123].{language}.vtt"
            subtitle_path.write_text(
                "WEBVTT\n\n00:00:00.000 --> 00:00:01.250\nManual caption\n",
                encoding="utf-8",
            )
            return {
                **info,
                "requested_subtitles": {
                    language: {
                        "ext": "vtt",
                        "filepath": str(subtitle_path),
                    }
                },
            }

    monkeypatch.setattr("podcast_to_text.youtube.YoutubeDL", FakeYoutubeDL)
    return calls
