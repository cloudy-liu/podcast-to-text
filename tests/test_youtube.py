from __future__ import annotations

from pathlib import Path

from podcast_to_text.youtube import YouTubeVideo, download_youtube_audio, is_youtube_url


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
