# Glossary

## Skill Project

The repository shape consumed by Claude Code, Codex, Cursor, opencode, or another AI coding agent as a skill: `SKILL.md`, `references/`, `scripts/`, and optional `agents/` metadata. The README remains the human-facing project introduction; the Python runtime lives under `scripts/`.

## Bundled CLI Runtime

The Python implementation under `scripts/podcast_to_text/`, invoked by the skill through `scripts/run_cli.py`. It handles source acquisition, YouTube subtitle extraction, audio fallback, local ASR, and raw subtitle artifact writing.

## Source Link

A Xiaoyuzhou episode URL or YouTube video URL provided by the user.

## Source Subtitle Artifact

The `source.srt` file that preserves the transcript closest to the media source, whether from platform subtitles or local ASR.

## Chinese Subtitle Artifact

The `transcript.zh.srt` file that represents the final Chinese subtitle for review and use.

## Chinese Insight Note

The `insights.md` file containing Chinese core insights extracted from the transcript.

## Final Result Area

The local git-ignored `output/result/` directory containing only lightweight final or partial result assets.

## Source-Only Partial Result

A retriable result state where `metadata.json` and `source.srt` exist but `transcript.zh.srt` has not yet been generated.

## Agent-Assisted Chinese Adaptation

Chinese translation, light correction, and mixed-language adaptation performed by the surrounding agent runtime, not by the Python CLI calling an external translation API.

## Transcription Calibration

Use source metadata and user-supplied vocabulary to improve source subtitle accuracy, Chinese adaptation, and insight extraction. For ASR, calibration means a short prompt derived from metadata, not raw metadata JSON.

## Calibration Prompt

The concise text passed to local ASR as `initial_prompt`. It may include user hints, source type, title, channel/uploader, and episode/video id.
