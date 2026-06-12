---
name: chinese-srt-adaptation
description: Convert a source-language `source.srt` transcript into `transcript.zh.srt` using the active Codex or Claude Code model, with no built-in LLM API client. Use when an episode/video output directory has `source.srt` and needs a Chinese SRT artifact that preserves cue count, order, and timestamps.
---

# Chinese SRT Adaptation

## Workflow

1. Locate the output directory and read `source.srt`.
2. Read `metadata.json` if present to understand provenance and source language.
3. Create `transcript.zh.srt` in the same directory.
4. Preserve every cue index and timestamp exactly.
5. Translate or correct only the cue text.
6. Run the bundled alignment validator before claiming completion.
7. Update `metadata.json` only after validation:
   - success: set `chinese_transcript.status` to `complete`
   - failure after a real attempt: set `chinese_transcript.status` to `failed`
   - skipped/no attempt: leave `pending`

Do not add API keys, base URLs, model names, or provider configuration to the project CLI. The active agent runtime supplies the language model.

## Text Rules

- English source text: translate into natural Chinese.
- Chinese source text: lightly correct recognition errors only.
- Mixed-language source text: translate the English portions and lightly correct Chinese portions.
- Preserve useful domain terms, person names, acronyms, product names, company names, library names, and command names in English when Chinese translation would reduce clarity.
- Do not summarize, merge cues, split cues, rewrite into article prose, add commentary, or change speaker meaning.
- Keep punctuation readable for subtitles; avoid long prose sentences if the original cue is short.

## SRT Rules

- Keep the same number of cues as `source.srt`.
- Keep cue indexes unchanged.
- Keep cue order unchanged.
- Keep every timestamp unchanged.
- Keep blank-line cue separation.
- Output only valid SRT content in `transcript.zh.srt`.

## Validation

Run this from the repository root or use absolute paths:

```powershell
python skills/chinese-srt-adaptation/scripts/validate_srt_alignment.py `
  path\to\source.srt `
  path\to\transcript.zh.srt
```

If validation fails, fix `transcript.zh.srt` and rerun. Do not mark the Chinese transcript complete until the validator exits 0.
