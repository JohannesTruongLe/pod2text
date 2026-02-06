from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from pod2text.env import get_openai_api_key, save_openai_api_key


def test_get_openai_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert get_openai_api_key(prompt_if_missing=False) == "sk-test"


def test_save_openai_api_key_creates_private_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    env_path = save_openai_api_key("sk-example")
    assert env_path == Path(".env")
    content = Path(".env").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY='sk-example'" in content

    mode = stat.S_IMODE(os.stat(".env").st_mode)
    assert mode & 0o077 == 0
