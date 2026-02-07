"""Telegram integration helpers."""

from __future__ import annotations

import time
from typing import Any

import requests

SEND_RETRY_ATTEMPTS = 3
SEND_RETRY_COOLDOWN_SECONDS = 2


def validate_bot_token(bot_token: str) -> dict[str, Any]:
    result = _telegram_call(bot_token, "getMe", {})
    if not isinstance(result, dict):
        raise ValueError("Unexpected getMe response from Telegram.")
    return result


def wait_for_chat_connection(bot_token: str, timeout_seconds: int = 60) -> tuple[str, str] | None:
    updates = _telegram_call(
        bot_token,
        "getUpdates",
        {
            "timeout": timeout_seconds,
            "allowed_updates": ["message", "channel_post"],
        },
        timeout_seconds=timeout_seconds + 10,
    )

    if not isinstance(updates, list):
        return None

    for update in reversed(updates):
        payload = update.get("message") or update.get("channel_post")
        if not payload:
            continue
        chat = payload.get("chat", {})
        chat_id = str(chat.get("id", "")).strip()
        if chat_id:
            return chat_id, _chat_name(chat)
    return None


def post_summary(bot_token: str, chat_id: str, summary: str) -> None:
    chunks = _chunk_text(summary, max_len=3900)
    for chunk in chunks:
        send_text(bot_token=bot_token, chat_id=chat_id, text=chunk)


def send_text(bot_token: str, chat_id: str, text: str) -> None:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    last_error: Exception | None = None

    for attempt in range(1, SEND_RETRY_ATTEMPTS + 1):
        try:
            _telegram_call(
                bot_token,
                "sendMessage",
                payload,
            )
            return
        except (ConnectionError, RuntimeError) as error:
            last_error = error
            if attempt == SEND_RETRY_ATTEMPTS:
                break
            time.sleep(SEND_RETRY_COOLDOWN_SECONDS * attempt)

    if last_error is not None:
        raise last_error


def poll_go_commands(
    bot_token: str,
    chat_id: str,
    offset: int | None = None,
    timeout_seconds: int = 5,
) -> tuple[bool, int | None]:
    payload: dict[str, Any] = {
        "timeout": timeout_seconds,
        "allowed_updates": ["message"],
    }
    if offset is not None:
        payload["offset"] = offset

    updates = _telegram_call(
        bot_token,
        "getUpdates",
        payload,
        timeout_seconds=timeout_seconds + 10,
    )
    if not isinstance(updates, list):
        return False, offset

    should_run = False
    next_offset = offset

    for update in updates:
        update_id = update.get("update_id")
        if isinstance(update_id, int):
            next_offset = update_id + 1

        message = update.get("message")
        if not isinstance(message, dict):
            continue

        update_chat_id = str(message.get("chat", {}).get("id", "")).strip()
        if update_chat_id != chat_id:
            continue

        text = str(message.get("text", "")).strip().lower()
        if text.startswith("/go"):
            should_run = True

    return should_run, next_offset


def _telegram_call(
    bot_token: str,
    method: str,
    payload: dict[str, Any],
    timeout_seconds: int = 30,
) -> Any:
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    try:
        response = requests.post(url, json=payload, timeout=timeout_seconds)
    except requests.ConnectionError as error:
        raise ConnectionError(
            f"Telegram {method} network error: unable to reach api.telegram.org"
        ) from error
    except requests.RequestException as error:
        raise RuntimeError(f"Telegram {method} request failed: {type(error).__name__}") from error

    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as error:
        raise ValueError(f"Telegram {method} returned invalid JSON.") from error

    if not data.get("ok"):
        description = data.get("description", "Unknown Telegram API error")
        raise ValueError(f"Telegram {method} failed: {description}")
    return data.get("result")


def _chat_name(chat: dict[str, Any]) -> str:
    for key in ("title", "username", "first_name"):
        value = str(chat.get(key, "")).strip()
        if value:
            return value
    return "unknown chat"


def _chunk_text(text: str, max_len: int) -> list[str]:
    content = text.strip()
    if not content:
        raise ValueError("Cannot send empty Telegram message.")
    if len(content) <= max_len:
        return [content]

    chunks: list[str] = []
    remaining = content
    while len(remaining) > max_len:
        split_at = remaining.rfind("\n\n", 0, max_len)
        if split_at <= 0:
            split_at = max_len
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks
