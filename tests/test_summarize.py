from __future__ import annotations

import pytest

from pod2text.summarize import summarize_transcript


def test_summarize_transcript_uses_openai_client(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyResponse:
        output_text = "# Episode Summary"

    class DummyResponses:
        @staticmethod
        def create(**_: object) -> DummyResponse:
            return DummyResponse()

    class DummyClient:
        def __init__(self, api_key: str) -> None:
            assert api_key == "sk-test"
            self.responses = DummyResponses()

    monkeypatch.setattr("pod2text.summarize.OpenAI", DummyClient)
    summary = summarize_transcript("hello world", api_key="sk-test")
    assert summary == "# Episode Summary"


def test_summarize_transcript_rejects_empty_text() -> None:
    with pytest.raises(ValueError):
        summarize_transcript("   ", api_key="sk-test")
