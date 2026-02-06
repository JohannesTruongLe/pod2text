"""Audio download helpers."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import requests

DEFAULT_BASENAME = "latest_episode"


def download_audio(audio_url: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    extension = _guess_extension(audio_url)
    target = output_dir / f"{DEFAULT_BASENAME}{extension}"

    with requests.get(audio_url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with target.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 512):
                if chunk:
                    file.write(chunk)
    return target


def _guess_extension(audio_url: str) -> str:
    path = urlparse(audio_url).path.lower()
    match = re.search(r"\.(mp3|m4a|aac|wav|ogg|flac)$", path)
    if match:
        return f".{match.group(1)}"
    return ".audio"
