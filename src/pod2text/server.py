"""Polling server for detecting new podcast episodes."""

from __future__ import annotations

import json
import time
from pathlib import Path

from pod2text.env import get_telegram_bot_token, get_telegram_chat_id
from pod2text.main import run_pipeline
from pod2text.podcast import fetch_latest_episode, resolve_feed_url
from pod2text.telegram import send_text


def run_server(
    podcast: str,
    output_dir: Path,
    transcription_model: str = "small",
    llm_model: str = "gpt-4o-mini",
    language: str = "de",
    interval_minutes: int = 30,
    state_file: Path = Path(".pod2text_state.json"),
    notify_startup: bool = True,
) -> None:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be greater than zero.")

    print(f"Starting pod2text server for '{podcast}' with {interval_minutes}-minute polling.")
    print(f"State file: {state_file}")
    if notify_startup:
        _send_startup_ready_message(podcast=podcast, interval_minutes=interval_minutes)

    while True:
        try:
            did_run = process_once(
                podcast=podcast,
                output_dir=output_dir,
                transcription_model=transcription_model,
                llm_model=llm_model,
                language=language,
                state_file=state_file,
            )
            if did_run:
                print("Pipeline completed for new episode.")
        except Exception as error:  # noqa: BLE001
            print(f"Polling error: {error}")
        time.sleep(interval_minutes * 60)


def process_once(
    podcast: str,
    output_dir: Path,
    transcription_model: str,
    llm_model: str,
    language: str,
    state_file: Path,
) -> bool:
    feed_url = resolve_feed_url(podcast)
    latest = fetch_latest_episode(feed_url)

    state = _load_state(state_file)
    last_id = state.get(feed_url)
    if last_id == latest.identifier:
        print(f"No new episode yet: {latest.title}")
        return False

    print(f"New episode detected: {latest.title}")
    run_pipeline(
        podcast=podcast,
        output_dir=output_dir,
        transcription_model=transcription_model,
        llm_model=llm_model,
        language=language,
        prompt_for_key=False,
    )
    state[feed_url] = latest.identifier
    _save_state(state_file, state)
    return True


def _load_state(state_file: Path) -> dict[str, str]:
    if not state_file.exists():
        return {}
    raw = json.loads(state_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    result: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str):
            result[key] = value
    return result


def _save_state(state_file: Path, state: dict[str, str]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _send_startup_ready_message(podcast: str, interval_minutes: int) -> None:
    text = (
        "pod2text is ready and setup.\n"
        f"Watching podcast: {podcast}\n"
        f"Polling interval: {interval_minutes} minutes"
    )
    send_text(
        bot_token=get_telegram_bot_token(),
        chat_id=get_telegram_chat_id(),
        text=text,
    )
