from __future__ import annotations

import json
from pathlib import Path

from pod2text.podcast import Episode
from pod2text.server import check_go_command_and_run, process_once, run_server


def test_process_once_runs_pipeline_for_new_episode(monkeypatch, tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    output_dir = tmp_path / "output"

    monkeypatch.setattr("pod2text.server.resolve_feed_url", lambda _: "https://feed.example.com")
    monkeypatch.setattr(
        "pod2text.server.fetch_latest_episode",
        lambda _: Episode(
            identifier="ep-1",
            title="Episode 1",
            audio_url="https://cdn.example.com/ep1.mp3",
            published=None,
        ),
    )

    called: list[str] = []

    def fake_run_pipeline(**_: object) -> tuple[Path, Path]:
        called.append("run")
        return output_dir / "latest_episode.mp3", output_dir / "summary.md"

    monkeypatch.setattr("pod2text.server.run_pipeline", fake_run_pipeline)

    did_run = process_once(
        podcast="Was jetzt",
        output_dir=output_dir,
        transcription_model="small",
        llm_model="gpt-4o-mini",
        language="de",
        state_file=state_file,
    )

    assert did_run is True
    assert called == ["run"]
    stored = json.loads(state_file.read_text(encoding="utf-8"))
    assert stored["episodes"]["https://feed.example.com"] == "ep-1"


def test_process_once_skips_known_episode(monkeypatch, tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"https://feed.example.com": "ep-1"}), encoding="utf-8")

    monkeypatch.setattr("pod2text.server.resolve_feed_url", lambda _: "https://feed.example.com")
    monkeypatch.setattr(
        "pod2text.server.fetch_latest_episode",
        lambda _: Episode(
            identifier="ep-1",
            title="Episode 1",
            audio_url="https://cdn.example.com/ep1.mp3",
            published=None,
        ),
    )

    called: list[str] = []

    def fake_run_pipeline(**_: object) -> tuple[Path, Path]:
        called.append("run")
        return Path("a"), Path("b")

    monkeypatch.setattr("pod2text.server.run_pipeline", fake_run_pipeline)

    did_run = process_once(
        podcast="Was jetzt",
        output_dir=tmp_path / "output",
        transcription_model="small",
        llm_model="gpt-4o-mini",
        language="de",
        state_file=state_file,
    )

    assert did_run is False
    assert called == []


def test_run_server_sends_ready_message_on_start(monkeypatch, tmp_path: Path) -> None:
    messages: list[str] = []

    monkeypatch.setattr("pod2text.server.get_telegram_bot_token", lambda: "token")
    monkeypatch.setattr("pod2text.server.get_telegram_chat_id", lambda: "chat-id")
    monkeypatch.setattr(
        "pod2text.server.send_text",
        lambda bot_token, chat_id, text: messages.append(f"{bot_token}:{chat_id}:{text}"),
    )
    monkeypatch.setattr("pod2text.server.process_once", lambda **_: False)

    def fake_sleep(_: int) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("pod2text.server.time.sleep", fake_sleep)

    try:
        run_server(
            podcast="Was jetzt",
            output_dir=tmp_path / "output",
            transcription_model="small",
            llm_model="gpt-4o-mini",
            language="de",
            interval_minutes=30,
            state_file=tmp_path / "state.json",
            notify_startup=True,
        )
    except KeyboardInterrupt:
        pass

    assert len(messages) == 1
    assert "ready and setup" in messages[0]


def test_check_go_command_triggers_pipeline(monkeypatch, tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"telegram_update_offset": 10}), encoding="utf-8")

    monkeypatch.setattr("pod2text.server.poll_go_commands", lambda **_: (True, 11))
    called: list[str] = []

    def fake_run_pipeline(**_: object) -> tuple[Path, Path]:
        called.append("run")
        return Path("a"), Path("b")

    monkeypatch.setattr("pod2text.server.run_pipeline", fake_run_pipeline)

    triggered, next_offset = check_go_command_and_run(
        podcast="Was jetzt",
        output_dir=tmp_path / "output",
        transcription_model="small",
        llm_model="gpt-4o-mini",
        language="de",
        state_file=state_file,
        bot_token="token",
        chat_id="chat-id",
        timeout_seconds=1,
    )

    assert triggered is True
    assert next_offset == 11
    assert called == ["run"]
