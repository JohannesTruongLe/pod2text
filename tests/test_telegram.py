from __future__ import annotations

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
