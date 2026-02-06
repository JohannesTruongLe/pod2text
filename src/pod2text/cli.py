"""Command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from pod2text.env import get_openai_api_key, save_openai_api_key
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
        prompt_for_key=True,
    )
    typer.echo(f"Downloaded audio: {audio_path}")
    typer.echo(f"Chapter summary: {summary_path}")


@app.command("setup-openai-key")
def setup_openai_key() -> None:
    existing = None
    try:
        existing = get_openai_api_key(prompt_if_missing=False)
    except ValueError:
        existing = None

    if existing:
        typer.echo("OPENAI_API_KEY is already configured in your environment/.env.")
        return

    key = typer.prompt("Enter your OpenAI API key", hide_input=True).strip()
    path = save_openai_api_key(key)
    typer.echo(f"Saved OPENAI_API_KEY to {path} with restrictive permissions.")


if __name__ == "__main__":
    app()
