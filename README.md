# pod2text

`pod2text` downloads the latest episode from a podcast feed and transcribes it with Whisper.

## Features

- Resolve known podcasts by name (currently includes `was jetzt`).
- Download the newest episode audio file from RSS/Atom feeds.
- Transcribe audio with local Whisper models.
- Simple CLI built with `typer`.

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- `ffmpeg` installed and available in your `PATH` (required by Whisper)

## Quickstart

```bash
uv sync
uv run pod2text transcribe --podcast "Was jetzt"
```

By default, outputs go into `./output`:

- `latest_episode.<ext>`: downloaded audio
- `transcript.txt`: plain-text transcript

## Usage

```bash
uv run pod2text transcribe \
  --podcast "Was jetzt" \
  --model "small" \
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

## Notes

- The `was jetzt` feed is resolved via an internal catalog entry.
- If you want more podcasts, add entries in `src/pod2text/catalog.py`.
