# Podcast To Text

`podcast-to-text` is a local command-line tool that turns a Xiaoyuzhou episode
link or YouTube video link into timestamped subtitle files.

It is designed for reviewable transcript workflows:

- Accept one Xiaoyuzhou episode URL or YouTube URL.
- Produce `source.srt`, a source-language subtitle artifact.
- Prefer existing YouTube platform subtitles before doing speech recognition.
- Fall back to local `faster-whisper` ASR when no usable platform subtitle exists.
- Record transcript provenance in `metadata.json`.
- Use the bundled agent skill to create `transcript.zh.srt` when a Chinese final
  subtitle artifact is needed.

The CLI does not include an LLM API client. Chinese translation or light
correction is handled by an agent runtime such as Codex or Claude Code using the
project skill in `skills/chinese-srt-adaptation/`.

## Quick Start

### 1. Prepare the Environment

Requirements:

- Python 3.10 or newer.
- Network access for Xiaoyuzhou/YouTube downloads.
- `ffmpeg` if you use `--limit-seconds` to create short audio samples.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Then install the project:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

### 2. Transcribe a YouTube Video

```powershell
python -m podcast_to_text.cli `
  "https://www.youtube.com/watch?v=jNQXAC9IVRw" `
  --out-dir out-youtube `
  --model small `
  --device cpu `
  --compute-type int8
```

YouTube runs use platform subtitles first. If no supported subtitle can be
downloaded, the CLI downloads audio and runs local ASR.

### 3. Transcribe a Xiaoyuzhou Episode

```powershell
python -m podcast_to_text.cli `
  "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2" `
  --out-dir out-xiaoyuzhou `
  --model small `
  --device cpu `
  --compute-type int8
```

For a quick smoke test, limit the run to the first 45 seconds:

```powershell
python -m podcast_to_text.cli `
  "https://www.xiaoyuzhoufm.com/episode/69b4d2f9f8b8079bfa3ae7f2" `
  --out-dir out-sample `
  --model small `
  --device cpu `
  --compute-type int8 `
  --limit-seconds 45
```

### 4. Create the Chinese Subtitle Artifact

The CLI stops at `source.srt`. To create `transcript.zh.srt`, use the bundled
skill with Codex or Claude Code:

```text
Use skills/chinese-srt-adaptation to convert <output-dir>/source.srt to
<output-dir>/transcript.zh.srt, then run the alignment validator.
```

The skill preserves cue count, order, and timestamps. It translates English
segments to Chinese, lightly corrects Chinese segments, and keeps domain terms
or names in English when that is clearer.

## Output Files

By default, each run creates a readable output directory:

```text
<out-dir>/<title>__<short-id>/
```

Each output directory contains:

- `metadata.json`: source metadata and transcript provenance.
- `source.srt`: source-language subtitle artifact.
- `segments.json`: parsed segment data.
- `audio_sample.wav` or downloaded source audio when local ASR runs.
- `transcript.zh.srt`: final Chinese subtitle artifact, created by the agent
  skill rather than by the CLI.

New code should not create the legacy `transcript.srt` or TXT transcript files.

## CLI Reference

```text
python -m podcast_to_text.cli <url> [options]
```

Common options:

| Option | Default | Description |
| --- | --- | --- |
| `url` | required | Xiaoyuzhou episode URL or YouTube URL. |
| `--out-dir` | `out` | Parent directory for generated artifacts. |
| `--model` | `medium` | `faster-whisper` model name, such as `tiny`, `small`, `medium`, or `large-v3`. |
| `--device` | `cpu` | Whisper device: `cpu`, `cuda`, or `auto`. |
| `--compute-type` | `int8` | Whisper compute type: `int8`, `float16`, `float32`, or `default`. |
| `--language` | `auto` | ASR language. `auto` keeps Xiaoyuzhou on Chinese and lets YouTube fallback ASR detect the source language. |
| `--beam-size` | `5` | Whisper beam size. Smaller values can be faster; larger values can be more thorough. |
| `--vad-filter` | off | Enable voice activity filtering in Whisper. |
| `--initial-prompt` | none | Vocabulary or context hint for names, products, and jargon. |
| `--dir-template` | `title-id` | Output directory naming: `title-id`, `id`, or `title`. |
| `--limit-seconds` | none | Transcribe only the first N seconds. Useful for testing. Requires `ffmpeg`. |

## Limits And Expectations

- The CLI processes one URL per command.
- Supported inputs are Xiaoyuzhou episode pages and YouTube watch, short, live,
  or `youtu.be` links.
- Xiaoyuzhou App-only transcript data is not fetched. The supported path is
  webpage/audio resolution plus local ASR.
- YouTube subtitle availability depends on the video. Subtitle downloads can
  also fail because of platform rate limits; the CLI tries the next subtitle
  candidate and then falls back to audio ASR.
- Local ASR quality depends on model size, audio quality, language, accents, and
  terminology. Use `--initial-prompt` for names and domain-specific vocabulary.
- CPU transcription can be slow, especially with larger models. Use `small` for
  quick tests and `large-v3` when quality matters more than runtime.
- The tool does not do speaker diarization, summarization, or article rewriting.
- `transcript.zh.srt` is generated by the agent skill, not by the CLI.

## How It Works

### Xiaoyuzhou

1. The CLI fetches the Xiaoyuzhou episode page.
2. It extracts episode metadata and the playable audio URL from the page.
3. It records any public transcript hints in `metadata.json`, but does not rely
   on private App transcript APIs.
4. It downloads the audio, or creates a short sample when `--limit-seconds` is
   used.
5. It runs local `faster-whisper` ASR and writes `source.srt`.

### YouTube

1. The CLI uses `yt-dlp` to inspect the video.
2. It tries platform subtitles before downloading audio.
3. Subtitle priority is:
   - manual Chinese
   - manual English
   - automatic Chinese
   - automatic English
4. Downloaded subtitles are normalized into `source.srt`.
5. If a subtitle candidate fails to download, the CLI tries the next candidate.
6. If no usable subtitle is available, the CLI downloads audio and runs local
   `faster-whisper` ASR.

## Chinese Adaptation Skill

The skill lives at:

```text
skills/chinese-srt-adaptation/
```

It instructs an agent to:

- read `source.srt`;
- create `transcript.zh.srt`;
- translate English text to Chinese;
- lightly correct existing Chinese text;
- preserve cue indexes, order, and timestamps;
- run `scripts/validate_srt_alignment.py` before marking metadata complete.

Run the validator directly when needed:

```powershell
python skills/chinese-srt-adaptation/scripts/validate_srt_alignment.py `
  path\to\source.srt `
  path\to\transcript.zh.srt
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
