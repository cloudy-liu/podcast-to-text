---
name: podcast-to-text
description: Use when an AI coding agent needs to transcribe, calibrate transcription, translate subtitles, extract Chinese insights, rebuild historical transcript outputs, or process Xiaoyuzhou/YouTube links through the bundled scripts runtime. Designed for Claude Code, Codex, Cursor, opencode, and similar agent runtimes. Final deliverables must be local Chinese transcript artifacts and Chinese insight notes.
---

# Podcast To Text

Use this repository as a portable agent skill for turning Xiaoyuzhou or YouTube source links into lightweight local Chinese transcript assets. The Python CLI is a bundled runtime under `scripts/`; the README remains the human-facing project introduction.

## Required Context

Read these references as needed:

- `references/output-policy.md` for final artifact rules.
- `references/transcription-calibration.md` for metadata-assisted ASR, Chinese adaptation, and insight calibration.
- `references/glossary.md` when changing transcript terminology or status language.
- `references/decisions.md` when changing project structure, CLI/runtime boundaries, or Chinese adaptation behavior.

## Workflow

1. Run the bundled CLI through `scripts/run_cli.py`. Do not reimplement Xiaoyuzhou parsing, YouTube extraction, or local ASR outside `scripts/podcast_to_text/`.

```bash
python scripts/run_cli.py "<source-link>"
```

2. Use source metadata for transcription calibration. The CLI converts Xiaoyuzhou/YouTube metadata into a short ASR prompt and records it in `metadata.json`; do not pass raw metadata JSON directly into ASR.
3. Generate or preserve the source-language subtitle as `source.srt`.
4. Generate the final Chinese subtitle as `transcript.zh.srt`.
   - If the source is Chinese, do light correction only.
   - If the source is non-Chinese, use agent-assisted segment-preserving Chinese adaptation.
   - Read `metadata.json` before adaptation so title, channel, episode/video id, source language, and calibration notes inform terminology choices.
   - Do not call external translation APIs by default; the surrounding agent/skill runtime performs the Chinese adaptation.
5. Write `insights.md` in Chinese. Use transcript content and source metadata together; do not leave English insight notes as final deliverables.
6. Copy only lightweight final assets into the local result directory `output/result/<title>__<short-id>/`: `metadata.json`, `source.srt` when available, `transcript.zh.srt`, and `insights.md`.
7. Remove large and intermediate files from final result directories: audio/video files, `.youtube-downloads`, `segments.json`, chunk folders, and legacy `transcript.srt`.
8. Update the local `output/result/manifest.md` when adding, completing, or marking partial historical results.
9. Validate before reporting completion:

```bash
python scripts/validate_result.py output/result
```

Use `--allow-partial` only when intentionally reporting source-only partial success:

```bash
python scripts/validate_result.py output/result --allow-partial
```

## Guardrails

- Historical transcript artifacts are important local assets. Do not delete them unless they are proven duplicate/redundant; preserve or ask when unsure.
- Keep `output/result/` local and small. It is ignored by git by default and should not be pushed unless the user explicitly asks to publish or export result artifacts.
- Treat `source.srt` without `transcript.zh.srt` as partial success, not completion.
- Keep the root directory lightweight. Put executable Python runtime code, dependencies, and tests under `scripts/`.
