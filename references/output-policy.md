# Output Policy

This policy defines what a completed local `output/result/<title>__<short-id>/` directory must contain. The `output/` tree is ignored by git by default and should not be pushed unless the user explicitly asks to publish or export result artifacts.

## Required Files

- `metadata.json`: source link, title, platform IDs, transcript source, transcription calibration, model/run metadata when available.
- `transcript.zh.srt`: the final Chinese subtitle artifact.
- `insights.md`: Chinese core insights extracted from the transcript.
- `source.srt`: preserve when the available source subtitle or ASR transcript is useful for audit, translation retry, or comparison.

## Allowed Partial Result

A source-only partial result may contain `metadata.json`, `source.srt`, and `insights.md` while `transcript.zh.srt` is pending. It must be described as partial and retriable, not complete.

## Forbidden In `output/result`

- Audio or video: `*.m4a`, `*.mp3`, `*.mp4`, `*.wav`, `*.webm`.
- Intermediates: `segments.json`, chunk folders, temporary downloads, `.youtube-downloads`.
- Legacy subtitle name: `transcript.srt`.
- Empty placeholder Chinese transcripts.

## Chinese Adaptation Rules

- Final insight notes must be Chinese.
- English or other non-Chinese source subtitles must become Chinese `transcript.zh.srt`.
- Preserve SRT segment count, order, and timestamps when adapting non-Chinese `source.srt`.
- Translate each segment according to its language mix. Preserve names, product names, company names, acronyms, and specialized terms when translating them would reduce clarity.
- For existing Chinese source subtitles, perform only light correction: obvious transcription errors, punctuation, spacing, and terminology. Do not summarize, expand, or rewrite into prose.
- Do not use Google Translate or other external translation APIs by default. The surrounding agent/skill runtime performs the adaptation.

## Manifest Rules

- Add every historical source link that should be rebuilt.
- Mark completed only when `transcript.zh.srt` and Chinese `insights.md` are present and validated.
- Mark source-only results as partial with the missing Chinese subtitle explicitly named.
