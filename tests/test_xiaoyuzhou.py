from podcast_to_text.xiaoyuzhou import (
    XiaoyuzhouEpisode,
    XiaoyuzhouTranscriptHint,
    is_xiaoyuzhou_episode_url,
    resolve_xiaoyuzhou_from_html,
)


def test_recognizes_xiaoyuzhou_episode_urls():
    assert is_xiaoyuzhou_episode_url(
        "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2"
    )
    assert is_xiaoyuzhou_episode_url(
        "https://xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2"
    )
    assert not is_xiaoyuzhou_episode_url("https://www.xiaoyuzhoufm.com/podcast/abc")


def test_extracts_og_audio_first():
    html = """
    <html>
      <head>
        <meta property="og:title" content="Episode Title">
        <meta property="og:audio" content="https://media.xyzcdn.net/example/audio.m4a">
        <script id="__NEXT_DATA__" type="application/json">
          {"props":{"pageProps":{"episode":{"eid":"eid-from-json","title":"JSON Title","enclosure":{"url":"https://media.xyzcdn.net/json.m4a"}}}}}
        </script>
      </head>
    </html>
    """

    episode = resolve_xiaoyuzhou_from_html(
        "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2",
        html,
    )

    assert episode == XiaoyuzhouEpisode(
        episode_id="eid-from-json",
        title="Episode Title",
        audio_url="https://media.xyzcdn.net/example/audio.m4a",
        source_url="https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2",
    )


def test_extracts_next_data_audio_when_og_audio_is_missing():
    html = """
    <html>
      <head>
        <script id="__NEXT_DATA__" type="application/json">
          {
            "props": {
              "pageProps": {
                "dehydratedState": {
                  "queries": [
                    {"state": {"data": {"episode": {
                      "eid": "json-eid",
                      "title": "JSON Episode",
                      "media": {"source": {"url": "https://media.xyzcdn.net/from-json.m4a"}}
                    }}}}
                  ]
                }
              }
            }
          }
        </script>
      </head>
    </html>
    """

    episode = resolve_xiaoyuzhou_from_html(
        "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2",
        html,
    )

    assert episode.episode_id == "json-eid"
    assert episode.title == "JSON Episode"
    assert episode.audio_url == "https://media.xyzcdn.net/from-json.m4a"


def test_extracts_xiaoyuzhou_transcript_hint_from_next_data():
    html = """
    <html>
      <head>
        <script id="__NEXT_DATA__" type="application/json">
          {
            "props": {
              "pageProps": {
                "episode": {
                  "eid": "json-eid",
                  "title": "JSON Episode",
                  "isTranscriptEnabled": true,
                  "transcript": {"mediaId": "fallback-media-id.m4a"},
                  "transcriptMediaId": "primary-media-id.m4a",
                  "media": {"source": {"url": "https://media.xyzcdn.net/from-json.m4a"}}
                }
              }
            }
          }
        </script>
      </head>
    </html>
    """

    episode = resolve_xiaoyuzhou_from_html(
        "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2",
        html,
    )

    assert episode.transcript_hint == XiaoyuzhouTranscriptHint(
        media_id="primary-media-id.m4a",
        is_enabled=True,
        has_marker=True,
        public_fetch_available=False,
    )


def test_extracts_xiaoyuzhou_transcript_hint_media_id_fallback():
    html = """
    <html>
      <head>
        <script id="__NEXT_DATA__" type="application/json">
          {
            "props": {
              "pageProps": {
                "episode": {
                  "eid": "json-eid",
                  "title": "JSON Episode",
                  "transcript": {"mediaId": "fallback-media-id.m4a"},
                  "media": {"source": {"url": "https://media.xyzcdn.net/from-json.m4a"}}
                }
              }
            }
          }
        </script>
      </head>
    </html>
    """

    episode = resolve_xiaoyuzhou_from_html(
        "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2",
        html,
    )

    assert episode.transcript_hint.media_id == "fallback-media-id.m4a"
    assert episode.transcript_hint.has_marker is True
    assert episode.transcript_hint.is_enabled is None
