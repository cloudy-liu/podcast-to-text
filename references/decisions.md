# Decisions

## 0001 README Remains The Project Introduction

Status: accepted

The README remains the human-facing project introduction and manual CLI guide. The repository also exposes a portable agent skill through `SKILL.md`, `references/`, `scripts/`, and optional `agents/` metadata so Claude Code, Codex, Cursor, opencode, and similar agent runtimes can run the fuller Chinese transcript workflow. Python packaging, tests, and the executable CLI live under `scripts/`.

Rejected alternative: replace the README with skill-only instructions. That makes the GitHub project page confusing for users who only want the CLI.

Consequence: users who clone the repository can run the CLI manually with `python scripts/run_cli.py`; agents can read `SKILL.md` for the higher-level workflow.

## 0002 CLI Owns Acquisition And ASR Only

Status: accepted

The bundled CLI runtime handles Xiaoyuzhou parsing, YouTube subtitle extraction, audio fallback, local ASR, metadata, and source subtitle artifacts. It does not own final Chinese adaptation or insight writing.

Consequence: the CLI writes `source.srt` for both platform subtitles and ASR output. The skill runtime produces `transcript.zh.srt` and Chinese `insights.md`.

## 0003 Chinese Adaptation Stays In The Agent Runtime

Status: accepted

Do not add built-in Google Translate or other external translation API clients to the CLI. English translation, Chinese light correction, and mixed-language subtitle adaptation are agent-assisted operations.

Consequence: skill users get consistent Chinese artifacts without provider configuration in the Python runtime.

## 0004 Store Lightweight Results Locally, Exclude Heavy Runtime Artifacts

Status: accepted

Keep `output/result/` as the local final result area and ignore it in git by default. Historical transcripts are valuable local assets, but they should not be pushed unless the user explicitly asks to publish or export them. Do not keep audio, video, chunks, `.youtube-downloads`, `segments.json`, or legacy `transcript.srt` in final result directories.

## 0005 Use Metadata-Derived Calibration, Not Raw Metadata Prompts

Status: accepted

Use Xiaoyuzhou and YouTube metadata to calibrate transcription and downstream Chinese adaptation. For local ASR, transform metadata into a concise prompt containing useful recognition hints such as source type, title, uploader/channel, source id, and user-provided vocabulary. Do not pass raw metadata JSON to ASR.

Consequence: `metadata.json` records `transcription_calibration` when local ASR uses the calibration prompt. The agent reads full metadata for Chinese adaptation and insight extraction.
