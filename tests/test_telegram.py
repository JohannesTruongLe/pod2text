from __future__ import annotations

from typing import Any

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
