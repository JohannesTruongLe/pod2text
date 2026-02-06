"""Pipeline orchestration."""

from __future__ import annotations

from pathlib import Path

from pod2text.download import download_audio
from pod2text.podcast import fetch_latest_episode, resolve_feed_url
from pod2text.transcribe import transcribe_audio


def run_pipeline(
    podcast: str,
    output_dir: Path,
    model: str = "small",
    language: str = "de",
) -> tuple[Path, Path]:
    feed_url = resolve_feed_url(podcast)
    episode = fetch_latest_episode(feed_url)
    audio_path = download_audio(episode.audio_url, output_dir)

    transcript = transcribe_audio(audio_path, model_name=model, language=language)
    transcript_path = output_dir / "transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")

    return audio_path, transcript_path
