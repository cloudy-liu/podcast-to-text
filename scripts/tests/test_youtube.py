from __future__ import annotations

from pathlib import Path

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
            output = Path(calls[0][1]["outtmpl"])
            audio_path = output.with_name("video audio [abc123].m4a")
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


def test_download_youtube_subtitle_prefers_manual_subtitles(monkeypatch, tmp_path):
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
            if download:
                subtitle_path = tmp_path / "video audio [abc123].zh-Hans.vtt"
                subtitle_path.write_text(
                    "WEBVTT\n\n"
                    "00:00:00.000 --> 00:00:01.250\n"
                    "Manual caption\n",
                    encoding="utf-8",
                )
            return {
                "id": "abc123",
                "title": "video audio",
                "webpage_url": "https://www.youtube.com/watch?v=abc123",
                "duration": 12.5,
                "uploader": "Example Channel",
                "subtitles": {
                    "zh-Hans": [{"ext": "vtt", "url": "https://example.test/zh.vtt"}],
                    "en": [{"ext": "vtt", "url": "https://example.test/manual.vtt"}]
                },
                "automatic_captions": {
                    "en": [{"ext": "vtt", "url": "https://example.test/auto.vtt"}]
                },
            }

    monkeypatch.setattr("podcast_to_text.youtube.YoutubeDL", FakeYoutubeDL)

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
    assert calls[1] == ("extract_info", "https://youtu.be/abc123", False)
    assert calls[2][1]["skip_download"] is True
    assert calls[2][1]["writesubtitles"] is True
    assert calls[2][1]["writeautomaticsub"] is False
    assert calls[2][1]["subtitleslangs"] == ["zh-Hans"]
    assert calls[3] == ("extract_info", "https://youtu.be/abc123", True)


def test_download_youtube_subtitle_falls_back_to_automatic_captions(monkeypatch, tmp_path):
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
            if download:
                subtitle_path = tmp_path / "video audio [abc123].en.vtt"
                subtitle_path.write_text(
                    "WEBVTT\n\n"
                    "00:00:00.000 --> 00:00:01.250\n"
                    "Automatic caption\n",
                    encoding="utf-8",
                )
            return {
                "id": "abc123",
                "title": "video audio",
                "webpage_url": "https://www.youtube.com/watch?v=abc123",
                "automatic_captions": {
                    "en": [{"ext": "vtt", "url": "https://example.test/auto.vtt"}]
                },
            }

    monkeypatch.setattr("podcast_to_text.youtube.YoutubeDL", FakeYoutubeDL)

    subtitle = download_youtube_subtitle("https://youtu.be/abc123", tmp_path)

    assert subtitle is not None
    assert subtitle.subtitle_type == "automatic"
    assert subtitle.language == "en"
    assert calls[1] == ("extract_info", "https://youtu.be/abc123", False)
    assert calls[2][1]["writesubtitles"] is False
    assert calls[2][1]["writeautomaticsub"] is True
    assert calls[2][1]["subtitleslangs"] == ["en"]
    assert calls[3] == ("extract_info", "https://youtu.be/abc123", True)


def test_download_youtube_subtitle_returns_none_when_no_supported_subtitles(monkeypatch, tmp_path):
    class FakeYoutubeDL:
        def __init__(self, options):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def extract_info(self, url, download):
            return {
                "id": "abc123",
                "title": "video audio",
                "webpage_url": "https://www.youtube.com/watch?v=abc123",
                "subtitles": {},
                "automatic_captions": {},
            }

    monkeypatch.setattr("podcast_to_text.youtube.YoutubeDL", FakeYoutubeDL)

    assert download_youtube_subtitle("https://youtu.be/abc123", tmp_path) is None
