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

For higher-quality Chinese podcast transcripts, use `large-v3` with a short
vocabulary prompt for names and jargon:

```powershell
.\.venv\Scripts\python.exe -m podcast_to_text.cli `
  "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2" `
  --model large-v3 --device cpu --compute-type int8 --beam-size 1 `
  --initial-prompt "Sheet0 OpenClaw AI Agent Manus product names and speaker names" `
  --limit-seconds 45 --out-dir out-large-v3
```

By default, each episode or video is written to a readable directory name:

```text
<out-dir>/<title>__<short-id>/
```

For example:

```text
out-large-v3/Example Episode Title__69b4d2f9/
```

Use `--dir-template id` if you want the legacy directory format:

```text
<out-dir>/<episode-id>/
```

## Artifact Contract

The public Source Link to `source.srt` workflow is:

1. Input is one Xiaoyuzhou or YouTube source link.
2. The CLI creates a readable output directory.
3. The CLI writes `source.srt` in the source language.
4. The agent skill creates `transcript.zh.srt` when a Chinese artifact is needed.

Each output directory contains:

- `metadata.json`
- `audio_sample.wav` or the downloaded original audio when local ASR runs
- `source.srt`
- `segments.json`

`transcript.srt` and TXT transcript outputs are deprecated and should not be
created by new code.

`metadata.json` records `source_transcript` provenance, including whether
`source.srt` came from a platform subtitle or local ASR and whether ASR was
used. It also records `chinese_transcript.status`; source-only CLI runs leave
that status as `pending` and do not create a fake `transcript.zh.srt`.

For YouTube videos with platform subtitles, `source.srt` is normalized from the
selected subtitle track and ASR is skipped. Subtitle priority is manual Chinese,
manual English, automatic Chinese, automatic English, then local ASR fallback.
When YouTube falls back to local ASR, the default `--language auto` lets Whisper
detect the spoken source language. Xiaoyuzhou keeps a Chinese ASR default unless
you pass an explicit language code.

## Chinese Adaptation

The CLI stops at `source.srt`. To create the final Chinese artifact, use the
project skill in `skills/chinese-srt-adaptation/` with Codex or Claude Code. The
skill transforms `source.srt` into `transcript.zh.srt`, preserves cue timing, and
runs its bundled SRT alignment validator. The CLI does not contain an LLM API
client, API key, base URL, or model provider configuration.

## Privacy Boundary

This repository is intended to contain source code, tests, public workflow
documentation, and reusable skills only. Do not commit local decision notes,
ADRs, local machine usage notes, generated media files, generated transcript
artifacts, or run logs.

Keep these local:

- `CONTEXT.md`
- `docs/adr/`
- `docs/superpowers/`
- local usage notes
- `output/`, `out*/`, `logs/`, `runs/`
- downloaded media files
- generated `source.srt`, `transcript.zh.srt`, legacy `transcript.srt`, and TXT transcripts

## Contribution Workflow

Work one vertical issue at a time:

1. Create or select one GitHub issue.
2. Create one branch for that issue.
3. Open one PR that closes that issue.
4. Merge the PR after verification.
5. Confirm the issue is closed before starting the next issue.

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
