"""Interactive setup wizard for OpenAI + Telegram credentials."""

from __future__ import annotations

from getpass import getpass

from pod2text.env import get_env_value, save_env_value
from pod2text.telegram import post_summary, validate_bot_token, wait_for_chat_connection


def run_setup_wizard() -> None:
    print("pod2text setup")
    print("This wizard configures OPENAI_API_KEY, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
    print("")

    _ensure_openai_key()
    bot_token = _ensure_telegram_bot_token()
    chat_id = _ensure_telegram_chat(bot_token)
    _send_test_message(bot_token, chat_id)
    print("")
    print("Setup complete. You can now run:")
    print('  uv run pod2text transcribe --podcast "Was jetzt"')


def _ensure_openai_key() -> None:
    existing = get_env_value("OPENAI_API_KEY")
    if existing:
        print("1. OPENAI_API_KEY already configured, skipping.")
        return

    print("1. Configure OpenAI API key")
    key = getpass("   Enter OPENAI_API_KEY: ").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY is required.")
    save_env_value("OPENAI_API_KEY", key)
    print("   Saved OPENAI_API_KEY to .env")


def _ensure_telegram_bot_token() -> str:
    existing = get_env_value("TELEGRAM_BOT_TOKEN")
    if existing:
        try:
            validate_bot_token(existing)
            print("2. TELEGRAM_BOT_TOKEN already configured and valid, skipping.")
            return existing
        except ValueError:
            print("2. Existing TELEGRAM_BOT_TOKEN is invalid, please enter a new one.")

    print("2. Configure Telegram bot token")
    print("   Create a bot via @BotFather and copy the token.")
    token = getpass("   Enter TELEGRAM_BOT_TOKEN: ").strip()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required.")

    me = validate_bot_token(token)
    username = me.get("username", "<unknown>")
    save_env_value("TELEGRAM_BOT_TOKEN", token)
    print(f"   Token validated for bot @{username} and saved to .env")
    return token


def _ensure_telegram_chat(bot_token: str) -> str:
    existing = get_env_value("TELEGRAM_CHAT_ID")
    if existing:
        print("3. TELEGRAM_CHAT_ID already configured, skipping.")
        return existing

    me = validate_bot_token(bot_token)
    username = me.get("username", "")
    print("3. Connect your Telegram chat")
    if username:
        print(f"   Open https://t.me/{username} and send any message to the bot.")
    else:
        print("   Send any message to your bot in Telegram.")
    input("   Press Enter once you sent the message... ")

    connection = wait_for_chat_connection(bot_token, timeout_seconds=60)
    if not connection:
        manual = input("   Could not auto-detect chat. Enter TELEGRAM_CHAT_ID manually: ").strip()
        if not manual:
            raise ValueError("TELEGRAM_CHAT_ID is required.")
        save_env_value("TELEGRAM_CHAT_ID", manual)
        print("   Saved TELEGRAM_CHAT_ID to .env")
        return manual

    chat_id, chat_name = connection
    save_env_value("TELEGRAM_CHAT_ID", chat_id)
    print(f"   Connected to chat '{chat_name}' (id: {chat_id}). Saved TELEGRAM_CHAT_ID.")
    return chat_id


def _send_test_message(bot_token: str, chat_id: str) -> None:
    print("4. Sending Telegram test message")
    post_summary(bot_token, chat_id, "pod2text setup complete. Telegram delivery is configured.")
    print("   Test message sent.")
