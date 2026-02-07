from __future__ import annotations

from typing import Any

import pytest
import requests

from pod2text.telegram import post_summary, wait_for_chat_connection


def test_wait_for_chat_connection_finds_latest_message(monkeypatch) -> None:
    def fake_call(*_: object, **__: object):
        return [
            {"update_id": 1, "message": {"chat": {"id": 111, "first_name": "Alice"}}},
            {"update_id": 2, "channel_post": {"chat": {"id": -222, "title": "News"}}},
        ]

    monkeypatch.setattr("pod2text.telegram._telegram_call", fake_call)
    assert wait_for_chat_connection("token", timeout_seconds=1) == ("-222", "News")


def test_post_summary_splits_large_messages(monkeypatch) -> None:
    sent: list[str] = []

    def fake_call(_: str, method: str, payload: dict, timeout_seconds: int = 30):
        assert method == "sendMessage"
        sent.append(payload["text"])
        return {}

    monkeypatch.setattr("pod2text.telegram._telegram_call", fake_call)
    long_text = ("Paragraph\n\n" * 900).strip()
    post_summary("token", "123", long_text)

    assert len(sent) > 1
    assert "".join(part.strip() for part in sent)


def test_poll_go_commands_filters_chat_and_tracks_offset(monkeypatch) -> None:
    from pod2text.telegram import poll_go_commands

    def fake_call(
        _: str, method: str, payload: dict[str, Any], timeout_seconds: int = 30
    ) -> list[dict[str, Any]]:
        assert method == "getUpdates"
        assert payload["offset"] == 7
        _ = timeout_seconds
        return [
            {"update_id": 7, "message": {"chat": {"id": 111}, "text": "/go"}},
            {"update_id": 8, "message": {"chat": {"id": 222}, "text": "/go"}},
            {"update_id": 9, "message": {"chat": {"id": 111}, "text": "hello"}},
        ]

    monkeypatch.setattr("pod2text.telegram._telegram_call", fake_call)
    should_run, next_offset = poll_go_commands(
        bot_token="token",
        chat_id="111",
        offset=7,
        timeout_seconds=1,
    )

    assert should_run is True
    assert next_offset == 10


def test_telegram_call_redacts_token_on_connection_error(monkeypatch) -> None:
    from pod2text.telegram import _telegram_call

    def fail_post(*_: object, **__: object):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr("pod2text.telegram.requests.post", fail_post)

    with pytest.raises(ConnectionError) as error:
        _telegram_call("super-secret-token", "getUpdates", {})

    message = str(error.value)
    assert "network error" in message
    assert "super-secret-token" not in message


def test_send_text_retries_and_succeeds(monkeypatch) -> None:
    from pod2text.telegram import send_text

    call_count = 0
    sleeps: list[int] = []

    def fake_call(*_: object, **__: object):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("temporary network issue")
        return {}

    monkeypatch.setattr("pod2text.telegram._telegram_call", fake_call)
    monkeypatch.setattr("pod2text.telegram.time.sleep", lambda seconds: sleeps.append(seconds))

    send_text("token", "chat-id", "hello")

    assert call_count == 3
    assert sleeps == [2, 4]


def test_send_text_retries_and_raises_after_exhaustion(monkeypatch) -> None:
    from pod2text.telegram import send_text

    call_count = 0
    sleeps: list[int] = []

    def fake_call(*_: object, **__: object):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("temporary request error")

    monkeypatch.setattr("pod2text.telegram._telegram_call", fake_call)
    monkeypatch.setattr("pod2text.telegram.time.sleep", lambda seconds: sleeps.append(seconds))

    with pytest.raises(RuntimeError):
        send_text("token", "chat-id", "hello")

    assert call_count == 3
    assert sleeps == [2, 4]
