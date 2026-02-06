# pod2text

`pod2text` downloads the latest episode from a podcast feed, transcribes it with Whisper, and summarizes it into digestible chapters using OpenAI.

## Features

- Resolve known podcasts by name (currently includes `was jetzt`).
- Download the newest episode audio file from RSS/Atom feeds.
- Transcribe audio with local Whisper models.
- Summarize transcripts into chaptered Markdown with an OpenAI model.
- Simple CLI built with `typer`.

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- `ffmpeg` installed and available in your `PATH` (required by Whisper)
- OpenAI API key

## Quickstart

```bash
uv sync
uv run pod2text setup-openai-key
uv run pod2text transcribe --podcast "Was jetzt"
```

By default, outputs go into `./output`:

- `latest_episode.<ext>`: downloaded audio
- `summary.md`: chaptered summary

## Usage

```bash
uv run pod2text transcribe \
  --podcast "Was jetzt" \
  --transcription-model "small" \
  --llm-model "gpt-4o-mini" \
  --language "de" \
  --output-dir "./output"
```

You can also pass a direct RSS URL:

```bash
uv run pod2text transcribe --podcast "https://example.com/feed.xml"
```

## Development

```bash
uv run pytest
uv run ruff check .
```

`setup-openai-key` stores your key in local `.env` as `OPENAI_API_KEY` and applies restrictive file permissions.

## Notes

- The `was jetzt` feed is resolved via an internal catalog entry.
- If you want more podcasts, add entries in `src/pod2text/catalog.py`.
