from podcast_to_text.outputs import Segment, render_srt, render_vtt_as_srt


def test_renders_srt_with_timestamps():
    segments = [
        Segment(start=0.0, end=1.25, text="第一段"),
        Segment(start=61.5, end=63.0, text="第二段"),
    ]

    assert render_srt(segments) == (
        "1\n"
        "00:00:00,000 --> 00:00:01,250\n"
        "第一段\n\n"
        "2\n"
        "00:01:01,500 --> 00:01:03,000\n"
        "第二段\n\n"
    )


def test_renders_vtt_as_srt():
    assert render_vtt_as_srt(
        "WEBVTT\n\n"
        "cue-id\n"
        "00:00:00.000 --> 00:00:01.250 align:start position:0%\n"
        "Manual caption\n\n"
        "00:00:02.500 --> 00:00:03.000\n"
        "Second line\n"
    ) == (
        "1\n"
        "00:00:00,000 --> 00:00:01,250\n"
        "Manual caption\n\n"
        "2\n"
        "00:00:02,500 --> 00:00:03,000\n"
        "Second line\n\n"
    )
