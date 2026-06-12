from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audio import extract_audio_sample
from .downloader import audio_extension, download_file, fetch_text
from .files import episode_directory_name
from .outputs import render_srt
from .transcriber import segments_to_jsonable, transcribe_audio
from .xiaoyuzhou import is_xiaoyuzhou_episode_url, resolve_xiaoyuzhou_from_html
from .youtube import download_youtube_audio, is_youtube_url


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe a Xiaoyuzhou episode or YouTube video link locally."
    )
    parser.add_argument("url", help="Xiaoyuzhou episode URL or YouTube URL")
    parser.add_argument("--out-dir", default="out", type=Path)
    parser.add_argument("--model", default="medium", help="faster-whisper model, e.g. tiny, small, medium, large-v3")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, or auto")
    parser.add_argument("--compute-type", default="int8", help="int8, float16, float32, or default")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--beam-size", default=5, type=int)
    parser.add_argument("--vad-filter", action="store_true")
    parser.add_argument("--initial-prompt", help="Vocabulary or context hint for Whisper, such as names and jargon")
    parser.add_argument(
        "--dir-template",
        default="title-id",
        choices=["title-id", "id", "title"],
        help="Output episode/video directory naming: title-id, id, or title",
    )
    parser.add_argument("--limit-seconds", type=float, help="Only transcribe the first N seconds for testing")
    args = parser.parse_args()

    episode_dir, metadata, audio_path = _prepare_input(args)

    segments, transcribe_metadata = transcribe_audio(
        audio_path,
        model_name=args.model,
        device=args.device,
        compute_type=args.compute_type,
        language=args.language,
        beam_size=args.beam_size,
        vad_filter=args.vad_filter,
        initial_prompt=args.initial_prompt,
    )
    metadata["transcription"] = transcribe_metadata
    metadata["audio_path"] = str(audio_path)

    (episode_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (episode_dir / "segments.json").write_text(
        json.dumps(segments_to_jsonable(segments), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (episode_dir / "transcript.srt").write_text(render_srt(segments), encoding="utf-8")

    print(json.dumps({"output_dir": str(episode_dir), **metadata}, ensure_ascii=False, indent=2))
    return 0


def _prepare_input(args: argparse.Namespace) -> tuple[Path, dict[str, object], Path]:
    if is_xiaoyuzhou_episode_url(args.url):
        return _prepare_xiaoyuzhou_input(args)

    if is_youtube_url(args.url):
        return _prepare_youtube_input(args)

    raise SystemExit("Only Xiaoyuzhou episode URLs and YouTube URLs are supported.")


def _prepare_xiaoyuzhou_input(args: argparse.Namespace) -> tuple[Path, dict[str, object], Path]:
    page_html = fetch_text(args.url)
    episode = resolve_xiaoyuzhou_from_html(args.url, page_html)
    episode_dir = args.out_dir / episode_directory_name(
        title=episode.title,
        episode_id=episode.episode_id,
        template=args.dir_template,
    )
    episode_dir.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, object] = {
        "source_type": "xiaoyuzhou",
        "source_url": episode.source_url,
        "episode_id": episode.episode_id,
        "title": episode.title,
        "audio_url": episode.audio_url,
        "limit_seconds": args.limit_seconds,
        "initial_prompt": args.initial_prompt,
        "platform_transcript_hint": episode.transcript_hint.to_jsonable(),
    }

    if args.limit_seconds:
        audio_path = episode_dir / "audio_sample.wav"
        extract_audio_sample(episode.audio_url, audio_path, args.limit_seconds)
    else:
        audio_path = episode_dir / f"audio{audio_extension(episode.audio_url)}"
        download_file(episode.audio_url, audio_path)

    return episode_dir, metadata, audio_path


def _prepare_youtube_input(args: argparse.Namespace) -> tuple[Path, dict[str, object], Path]:
    staging_dir = args.out_dir / ".youtube-downloads"
    staging_dir.mkdir(parents=True, exist_ok=True)
    video = download_youtube_audio(args.url, staging_dir)
    video_dir = args.out_dir / episode_directory_name(
        title=video.title,
        episode_id=video.video_id,
        template=args.dir_template,
    )
    video_dir.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, object] = {
        "source_type": "youtube",
        "source_url": video.source_url,
        "video_id": video.video_id,
        "title": video.title,
        "webpage_url": video.webpage_url,
        "duration": video.duration,
        "uploader": video.uploader,
        "limit_seconds": args.limit_seconds,
        "initial_prompt": args.initial_prompt,
    }

    if args.limit_seconds:
        audio_path = video_dir / "audio_sample.wav"
        extract_audio_sample(str(video.audio_path), audio_path, args.limit_seconds)
        _delete_if_exists(video.audio_path)
    else:
        audio_path = video_dir / video.audio_path.name
        if video.audio_path.resolve() != audio_path.resolve():
            video.audio_path.replace(audio_path)

    _delete_dir_if_empty(staging_dir)
    return video_dir, metadata, audio_path


def _delete_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def _delete_dir_if_empty(path: Path) -> None:
    try:
        path.rmdir()
    except OSError:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
