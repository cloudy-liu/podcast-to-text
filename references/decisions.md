# Decisions

## 0001 Portable Agent Skill Is The Primary Surface

Status: accepted

The repository is structured as a portable agent skill project. Claude Code, Codex, Cursor, opencode, and similar agent runtimes can consume the root `SKILL.md`, `references/`, `scripts/`, and optional `agents/` metadata. Python packaging, tests, and the executable CLI live under `scripts/`.

Rejected alternative: keep a normal Python CLI project at the root and add `SKILL.md` as a wrapper. That makes users see the project as a CLI first, which conflicts with the intended skill-first distribution model.

Consequence: users who clone the repository can still run the CLI manually by entering `scripts/` or calling `python scripts/run_cli.py`, but the skill instructions remain the main interface.

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
