"""Pipeline orchestration."""

from __future__ import annotations

from pathlib import Path

from pod2text.download import download_audio
from pod2text.env import get_openai_api_key, get_telegram_bot_token, get_telegram_chat_id
from pod2text.podcast import fetch_latest_episode, resolve_feed_url
from pod2text.summarize import summarize_transcript
from pod2text.telegram import post_summary
from pod2text.transcribe import transcribe_audio


def run_pipeline(
    podcast: str,
    output_dir: Path,
    transcription_model: str = "small",
    llm_model: str = "gpt-4o-mini",
    language: str = "de",
    prompt_for_key: bool = True,
) -> tuple[Path, Path]:
    feed_url = resolve_feed_url(podcast)
    episode = fetch_latest_episode(feed_url)
    audio_path = download_audio(episode.audio_url, output_dir)

    transcript = transcribe_audio(audio_path, model_name=transcription_model, language=language)
    api_key = get_openai_api_key(prompt_if_missing=prompt_for_key)
    summary = summarize_transcript(transcript, api_key=api_key, model=llm_model)
    summary_path = output_dir / "summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    post_summary(
        bot_token=get_telegram_bot_token(),
        chat_id=get_telegram_chat_id(),
        summary=summary,
        episode_title=episode.title,
    )

    return audio_path, summary_path
