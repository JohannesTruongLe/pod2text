#!/usr/bin/env python3
"""Standalone setup wizard for .env without project dependencies."""

from __future__ import annotations

import json
import os
import stat
import sys
import urllib.error
import urllib.request
from getpass import getpass
from pathlib import Path
from typing import Any

ENV_PATH = Path(".env")


def main() -> int:
    env = load_env_file(ENV_PATH)

    print("pod2text setup")
    print("This configures OPENAI_API_KEY, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
    print("")

    ensure_openai_key(env)
    bot_token = ensure_telegram_bot_token(env)
    ensure_telegram_chat_id(env, bot_token)
    save_env_file(ENV_PATH, env)

    print("")
    print("Setup complete. You can now run:")
    print("  ./scripts/deploy_docker.sh")
    return 0


def ensure_openai_key(env: dict[str, str]) -> None:
    if env.get("OPENAI_API_KEY", "").strip():
        print("1. OPENAI_API_KEY already configured, skipping.")
        return

    print("1. Configure OpenAI API key")
    key = getpass("   Enter OPENAI_API_KEY: ").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY is required.")
    env["OPENAI_API_KEY"] = key
    print("   Saved OPENAI_API_KEY")


def ensure_telegram_bot_token(env: dict[str, str]) -> str:
    existing = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    if existing:
        try:
            me = telegram_api(existing, "getMe", {})
            username = str(me.get("username", "<unknown>"))
            print(f"2. TELEGRAM_BOT_TOKEN already configured and valid (@{username}), skipping.")
            return existing
        except Exception:
            print("2. Existing TELEGRAM_BOT_TOKEN is invalid. Please enter a new token.")

    print("2. Configure Telegram bot token")
    print("   Create a bot via @BotFather and paste the token.")
    token = getpass("   Enter TELEGRAM_BOT_TOKEN: ").strip()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required.")

    me = telegram_api(token, "getMe", {})
    username = str(me.get("username", "<unknown>"))
    env["TELEGRAM_BOT_TOKEN"] = token
    print(f"   Token validated for bot @{username}")
    return token


def ensure_telegram_chat_id(env: dict[str, str], bot_token: str) -> None:
    existing = env.get("TELEGRAM_CHAT_ID", "").strip()
    if existing:
        print("3. TELEGRAM_CHAT_ID already configured, skipping.")
        send_test_message(bot_token, existing)
        return

    me = telegram_api(bot_token, "getMe", {})
    username = str(me.get("username", "")).strip()

    print("3. Connect your Telegram chat")
    if username:
        print(f"   Open https://t.me/{username} and send any message to the bot.")
    else:
        print("   Send any message to your bot in Telegram.")
    input("   Press Enter once you sent the message... ")

    updates = telegram_api(
        bot_token,
        "getUpdates",
        {"timeout": 20, "allowed_updates": ["message", "channel_post"]},
        timeout_seconds=30,
    )
    chat = extract_latest_chat(updates)

    if chat is None:
        manual = input("   Could not auto-detect chat. Enter TELEGRAM_CHAT_ID manually: ").strip()
        if not manual:
            raise ValueError("TELEGRAM_CHAT_ID is required.")
        env["TELEGRAM_CHAT_ID"] = manual
        print("   Saved TELEGRAM_CHAT_ID")
        send_test_message(bot_token, manual)
        return

    chat_id, chat_name = chat
    env["TELEGRAM_CHAT_ID"] = chat_id
    print(f"   Connected to chat '{chat_name}' (id: {chat_id})")
    send_test_message(bot_token, chat_id)


def send_test_message(bot_token: str, chat_id: str) -> None:
    print("4. Sending Telegram test message")
    telegram_api(
        bot_token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": "pod2text setup complete. Telegram delivery is configured.",
            "disable_web_page_preview": True,
        },
    )
    print("   Test message sent.")


def extract_latest_chat(updates: Any) -> tuple[str, str] | None:
    if not isinstance(updates, list):
        return None
    for update in reversed(updates):
        if not isinstance(update, dict):
            continue
        payload = update.get("message") or update.get("channel_post")
        if not isinstance(payload, dict):
            continue
        chat = payload.get("chat", {})
        if not isinstance(chat, dict):
            continue
        chat_id = str(chat.get("id", "")).strip()
        if not chat_id:
            continue
        for key in ("title", "username", "first_name"):
            name = str(chat.get(key, "")).strip()
            if name:
                return chat_id, name
        return chat_id, "unknown chat"
    return None


def telegram_api(
    bot_token: str,
    method: str,
    payload: dict[str, Any],
    timeout_seconds: int = 15,
) -> Any:
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as error:
        raise ValueError(f"Telegram API HTTP error: {error.code}") from error

    data = json.loads(raw.decode("utf-8"))
    if not data.get("ok"):
        description = data.get("description", "Unknown Telegram API error")
        raise ValueError(f"Telegram {method} failed: {description}")
    return data.get("result")


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            env[key] = value
    return env


def save_env_file(path: Path, env: dict[str, str]) -> None:
    lines = [f"{key}='{escape_env_value(env[key])}'" for key in sorted(env)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def escape_env_value(value: str) -> str:
    return value.replace("'", "'\"'\"'")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nAborted.")
        raise SystemExit(130) from None
    except Exception as error:  # noqa: BLE001
        print(f"Setup failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
