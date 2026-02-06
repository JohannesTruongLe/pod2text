"""Whisper-based transcription."""

from __future__ import annotations

from pathlib import Path

import whisper


def transcribe_audio(
    audio_path: Path,
    model_name: str = "small",
    language: str = "de",
) -> str:
    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path), language=language)
    text = result.get("text", "").strip()
    if not text:
        raise ValueError("Transcription returned no text.")
    return text
