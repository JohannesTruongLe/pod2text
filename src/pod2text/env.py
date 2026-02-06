"""Environment and secret handling."""

from __future__ import annotations

import os
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv, set_key

ENV_FILE = Path(".env")


def get_env_value(name: str) -> str:
    load_dotenv()
    return os.getenv(name, "").strip()


def save_env_value(name: str, value: str) -> Path:
    text = value.strip()
    if not text:
        raise ValueError(f"{name} cannot be empty.")
    set_key(str(ENV_FILE), name, text)
    os.chmod(ENV_FILE, 0o600)
    return ENV_FILE


def get_openai_api_key(prompt_if_missing: bool = False) -> str:
    key = get_env_value("OPENAI_API_KEY")
    if key:
        return key

    if not prompt_if_missing:
        raise ValueError(
            "OPENAI_API_KEY is not configured. Run `uv run python scripts/setup_env.py` first."
        )

    entered = getpass("Enter your OpenAI API key: ").strip()
    if not entered:
        raise ValueError("No API key entered.")
    save_openai_api_key(entered)
    return entered


def save_openai_api_key(api_key: str) -> Path:
    return save_env_value("OPENAI_API_KEY", api_key)


def get_telegram_bot_token() -> str:
    token = get_env_value("TELEGRAM_BOT_TOKEN")
    if token:
        return token
    raise ValueError(
        "TELEGRAM_BOT_TOKEN is not configured. Run `uv run python scripts/setup_env.py` first."
    )


def get_telegram_chat_id() -> str:
    chat_id = get_env_value("TELEGRAM_CHAT_ID")
    if chat_id:
        return chat_id
    raise ValueError(
        "TELEGRAM_CHAT_ID is not configured. Run `uv run python scripts/setup_env.py` first."
    )
