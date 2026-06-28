# Transcription Calibration

Transcription calibration uses source metadata to improve three stages: local ASR, segment-level Chinese adaptation, and Chinese insight extraction.

## Metadata Sources

- Xiaoyuzhou: title, episode id, source URL, audio URL, and platform transcript hint when available.
- YouTube: title, video id, webpage URL, duration, uploader/channel, platform subtitle language, and subtitle type.
- User prompt: names, companies, products, technical terms, jargon, and spelling hints supplied through `--initial-prompt` or the user request.

## ASR Calibration

Pass only a concise calibration prompt to ASR. The bundled CLI builds this prompt from:

- `User hint: ...`
- `Source type: ...`
- `Title: ...`
- `Channel: ...`
- `Source id: ...`

Do not pass raw metadata JSON, full URLs, descriptions, long show notes, or previous transcripts directly to ASR. They add noise and can reduce recognition quality.

When ASR uses this prompt, `metadata.json` must include:

```json
{
  "transcription_calibration": {
    "artifact": "metadata.json",
    "method": "source_metadata_prompt",
    "used_for_asr": true,
    "prompt": "..."
  }
}
```

## Chinese Adaptation Calibration

Before generating `transcript.zh.srt`, read `metadata.json` and `source.srt` together.

- Use the title and uploader/channel to disambiguate names and topics.
- Preserve product names, company names, acronyms, and speaker names when translating them would reduce clarity.
- Keep SRT segment count, order, and timestamps unchanged.
- Treat source-only results as partial if metadata or source subtitles exist but Chinese subtitles are not done.

## Insight Calibration

Use metadata to frame the Chinese `insights.md`, but ground claims in the transcript. The title and platform metadata can identify topic and speaker context; they must not replace transcript evidence.
