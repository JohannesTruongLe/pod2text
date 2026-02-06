"""Polling server for detecting new podcast episodes."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pod2text.env import get_telegram_bot_token, get_telegram_chat_id
from pod2text.main import run_pipeline
from pod2text.podcast import fetch_latest_episode, resolve_feed_url
from pod2text.telegram import poll_go_commands, send_text

STATE_EPISODES_KEY = "episodes"
STATE_TELEGRAM_OFFSET_KEY = "telegram_update_offset"


def run_server(
    podcast: str,
    output_dir: Path,
    transcription_model: str = "small",
    llm_model: str = "gpt-4o-mini",
    language: str = "de",
    interval_minutes: int = 30,
    telegram_poll_seconds: int = 5,
    state_file: Path = Path(".pod2text_state.json"),
    notify_startup: bool = True,
) -> None:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be greater than zero.")
    if telegram_poll_seconds <= 0:
        raise ValueError("telegram_poll_seconds must be greater than zero.")

    print(f"Starting pod2text server for '{podcast}' with {interval_minutes}-minute polling.")
    print(f"State file: {state_file}")
    bot_token = get_telegram_bot_token()
    chat_id = get_telegram_chat_id()

    if notify_startup:
        _send_startup_ready_message(
            podcast=podcast,
            interval_minutes=interval_minutes,
            bot_token=bot_token,
            chat_id=chat_id,
        )

    next_episode_check_at = 0.0
    while True:
        try:
            go_triggered, update_offset = check_go_command_and_run(
                podcast=podcast,
                output_dir=output_dir,
                transcription_model=transcription_model,
                llm_model=llm_model,
                language=language,
                state_file=state_file,
                bot_token=bot_token,
                chat_id=chat_id,
                timeout_seconds=telegram_poll_seconds,
            )
            if go_triggered:
                print("Pipeline completed after /go command.")

            now = time.time()
            if now >= next_episode_check_at:
                did_run = process_once(
                    podcast=podcast,
                    output_dir=output_dir,
                    transcription_model=transcription_model,
                    llm_model=llm_model,
                    language=language,
                    state_file=state_file,
                )
                next_episode_check_at = now + interval_minutes * 60
                if did_run:
                    print("Pipeline completed for new episode.")

            if update_offset is not None:
                _save_telegram_update_offset(state_file, update_offset)

            time.sleep(telegram_poll_seconds)
        except Exception as error:  # noqa: BLE001
            print(f"Polling error: {error}")
            time.sleep(telegram_poll_seconds)


def check_go_command_and_run(
    podcast: str,
    output_dir: Path,
    transcription_model: str,
    llm_model: str,
    language: str,
    state_file: Path,
    bot_token: str,
    chat_id: str,
    timeout_seconds: int,
) -> tuple[bool, int | None]:
    offset = _load_telegram_update_offset(state_file)
    should_run, next_offset = poll_go_commands(
        bot_token=bot_token,
        chat_id=chat_id,
        offset=offset,
        timeout_seconds=timeout_seconds,
    )
    if not should_run:
        return False, next_offset

    print("Received /go command from Telegram. Running pipeline now.")
    run_pipeline(
        podcast=podcast,
        output_dir=output_dir,
        transcription_model=transcription_model,
        llm_model=llm_model,
        language=language,
        prompt_for_key=False,
    )
    return True, next_offset


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
    episodes = _get_episodes_map(state)
    last_id = episodes.get(feed_url)
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
    episodes[feed_url] = latest.identifier
    state[STATE_EPISODES_KEY] = episodes
    _save_state(state_file, state)
    return True


def _load_state(state_file: Path) -> dict[str, Any]:
    if not state_file.exists():
        return {STATE_EPISODES_KEY: {}}
    raw = json.loads(state_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {STATE_EPISODES_KEY: {}}

    # Backward compatibility: previous versions stored `{feed_url: episode_id}` flat.
    if STATE_EPISODES_KEY not in raw:
        episodes: dict[str, str] = {}
        for key, value in raw.items():
            if isinstance(key, str) and isinstance(value, str):
                episodes[key] = value
        return {STATE_EPISODES_KEY: episodes}

    return raw


def _save_state(state_file: Path, state: dict[str, Any]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _get_episodes_map(state: dict[str, Any]) -> dict[str, str]:
    raw = state.get(STATE_EPISODES_KEY, {})
    if not isinstance(raw, dict):
        return {}
    result: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str):
            result[key] = value
    return result


def _load_telegram_update_offset(state_file: Path) -> int | None:
    state = _load_state(state_file)
    raw = state.get(STATE_TELEGRAM_OFFSET_KEY)
    if isinstance(raw, int):
        return raw
    return None


def _save_telegram_update_offset(state_file: Path, offset: int) -> None:
    state = _load_state(state_file)
    state[STATE_TELEGRAM_OFFSET_KEY] = offset
    _save_state(state_file, state)


def _send_startup_ready_message(
    podcast: str,
    interval_minutes: int,
    bot_token: str,
    chat_id: str,
) -> None:
    text = (
        "pod2text is ready and setup.\n"
        f"Watching podcast: {podcast}\n"
        f"Polling interval: {interval_minutes} minutes\n"
        "Send /go to trigger an immediate run."
    )
    send_text(
        bot_token=bot_token,
        chat_id=chat_id,
        text=text,
    )
