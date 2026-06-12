from podcast_to_text.outputs import (
    Segment,
    normalize_subtitle_to_srt,
    parse_subtitle_segments,
    render_srt,
)


def test_renders_srt_with_timestamps():
    segments = [
        Segment(start=0.0, end=1.25, text="first segment"),
        Segment(start=61.5, end=63.0, text="second segment"),
    ]

    assert render_srt(segments) == (
        "1\n"
        "00:00:00,000 --> 00:00:01,250\n"
        "first segment\n\n"
        "2\n"
        "00:01:01,500 --> 00:01:03,000\n"
        "second segment\n\n"
    )


def test_normalizes_vtt_to_srt():
    source = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:01.250 align:start position:0%\n"
        "<c>Manual caption</c>\n\n"
        "00:00:01.250 --> 00:00:03.000\n"
        "Second &amp; caption\n"
    )

    assert normalize_subtitle_to_srt(source) == (
        "1\n"
        "00:00:00,000 --> 00:00:01,250\n"
        "Manual caption\n\n"
        "2\n"
        "00:00:01,250 --> 00:00:03,000\n"
        "Second & caption\n\n"
    )


def test_parses_existing_srt_segments():
    source = (
        "1\n"
        "00:00:00,000 --> 00:00:01,250\n"
        "Manual caption\n"
    )

    assert parse_subtitle_segments(source) == [
        Segment(start=0.0, end=1.25, text="Manual caption")
    ]
