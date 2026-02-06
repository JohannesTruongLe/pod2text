"""Command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from pod2text.main import run_pipeline

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def main() -> None:
    """pod2text command line."""


@app.command()
def transcribe(
    podcast: Annotated[
        str, typer.Option(..., help="Podcast name from catalog or direct RSS URL.")
    ],
    output_dir: Annotated[
        Path,
        typer.Option(help="Directory for downloaded audio and transcript."),
    ] = Path("./output"),
    model: Annotated[
        str, typer.Option(help="Whisper model size, e.g. tiny/base/small/medium.")
    ] = "small",
    language: Annotated[str, typer.Option(help="Language code used by Whisper.")] = "de",
) -> None:
    audio_path, transcript_path = run_pipeline(
        podcast=podcast,
        output_dir=output_dir,
        model=model,
        language=language,
    )
    typer.echo(f"Downloaded audio: {audio_path}")
    typer.echo(f"Transcript: {transcript_path}")


if __name__ == "__main__":
    app()
