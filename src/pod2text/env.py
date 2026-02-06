"""Environment and secret handling."""

from __future__ import annotations

import os
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv, set_key

ENV_FILE = Path(".env")


def get_openai_api_key(prompt_if_missing: bool = False) -> str:
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key

    if not prompt_if_missing:
        raise ValueError(
            "OPENAI_API_KEY is not configured. Run `pod2text setup-openai-key` first."
        )

    entered = getpass("Enter your OpenAI API key: ").strip()
    if not entered:
        raise ValueError("No API key entered.")
    save_openai_api_key(entered)
    return entered


def save_openai_api_key(api_key: str) -> Path:
    key = api_key.strip()
    if not key:
        raise ValueError("API key cannot be empty.")

    set_key(str(ENV_FILE), "OPENAI_API_KEY", key)
    os.chmod(ENV_FILE, 0o600)
    return ENV_FILE
