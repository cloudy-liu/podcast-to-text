# Podcast To Text

Local Xiaoyuzhou and YouTube transcription with `faster-whisper`.

## Quick Start

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m podcast_to_text.cli `
  "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2" `
  --model small --device cpu --compute-type int8 --limit-seconds 45 --out-dir out-small
```

YouTube links use `yt-dlp` to fetch platform subtitles first. If no supported
Chinese or English subtitle is available, the CLI downloads audio and runs the
same local ASR path:

```powershell
.\.venv\Scripts\python.exe -m podcast_to_text.cli `
  "https://www.youtube.com/watch?v=jNQXAC9IVRw" `
  --model small --device cpu --compute-type int8 --limit-seconds 45 --out-dir out-youtube
```

For higher-quality Chinese podcast transcripts on this machine, use `large-v3`
with a short vocabulary prompt for names and jargon:

```powershell
.\.venv\Scripts\python.exe -m podcast_to_text.cli `
  "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2" `
  --model large-v3 --device cpu --compute-type int8 --beam-size 1 `
  --initial-prompt "世界零 Sheet0 创始人王文锋 曲凯 AI Agent Manus" `
  --limit-seconds 45 --out-dir out-large-v3
```

By default, each episode or video is written to a readable directory name:

```text
<out-dir>/<title>__<short-id>/
```

For example:

```text
out-large-v3/OpenClaw 之后，我只想未来 3-6 个月的事情｜对谈 Sheet0 创始人王文锋__69b4d2f9/
```

Use `--dir-template id` if you want the legacy directory format:

```text
<out-dir>/<episode-id>/
```

Each output directory contains:

- `metadata.json`
- `audio_sample.wav` or the downloaded original audio
- `source.srt`
- `segments.json`

For YouTube videos with platform subtitles, `source.srt` is normalized from the
selected subtitle track and ASR is skipped. Subtitle priority is manual Chinese,
manual English, automatic Chinese, automatic English, then local ASR fallback.

## Xiaoyuzhou Transcript Hints

Some Xiaoyuzhou episode pages expose transcript metadata such as
`transcriptMediaId`, but the public web page does not expose the transcript
sentences. When present, the CLI records this clue in `metadata.json`:

```json
{
  "platform_transcript_hint": {
    "source": "xiaoyuzhou_next_data",
    "media_id": "626b46ea9cbbf0451cf5a962/lg4SPHlAUnrJuULqRaXS_1Gc5ufZ.m4a",
    "is_enabled": null,
    "has_marker": true,
    "public_fetch_available": false
  }
}
```

The project treats this as metadata only. Public unauthenticated transcript
fetching is not a planned dependency because the App/API transcript endpoint
appears to require Xiaoyuzhou login/device credentials. The supported path is
local `faster-whisper` transcription from the episode audio.
