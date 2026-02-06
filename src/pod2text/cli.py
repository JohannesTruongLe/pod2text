"""Command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from pod2text.main import run_pipeline
from pod2text.setup_wizard import run_setup_wizard

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
        typer.Option(help="Directory for downloaded audio and summary."),
    ] = Path("./output"),
    transcription_model: Annotated[
        str, typer.Option(help="Whisper model size, e.g. tiny/base/small/medium.")
    ] = "small",
    llm_model: Annotated[
        str, typer.Option(help="OpenAI model for chaptered summarization.")
    ] = "gpt-4o-mini",
    language: Annotated[str, typer.Option(help="Language code used by Whisper.")] = "de",
) -> None:
    audio_path, summary_path = run_pipeline(
        podcast=podcast,
        output_dir=output_dir,
        transcription_model=transcription_model,
        llm_model=llm_model,
        language=language,
        prompt_for_key=False,
    )
    typer.echo(f"Downloaded audio: {audio_path}")
    typer.echo(f"Chapter summary: {summary_path}")
    typer.echo("Summary was posted to Telegram.")


@app.command("setup")
def setup() -> None:
    run_setup_wizard()


if __name__ == "__main__":
    app()
