# pod2text

`pod2text` downloads the latest episode from a podcast feed, transcribes it with Whisper, summarizes it with OpenAI, and posts the summary to Telegram.

## Features

- Resolve known podcasts by name (currently includes `was jetzt`).
- Download the newest episode audio file from RSS/Atom feeds.
- Transcribe audio with local Whisper models.
- Summarize transcripts into chaptered Markdown with an OpenAI model.
- Automatically post each summary to your Telegram chat.
- Simple CLI built with `typer`.

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- `ffmpeg` installed and available in your `PATH` (required by Whisper)
- OpenAI API key
- Telegram bot token and target chat ID

## Quickstart

```bash
uv sync
uv run python scripts/setup_env.py
# alternatively: uv run pod2text setup
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

Run as a server (poll every 30 minutes and run only on new episodes):

```bash
uv run pod2text serve --podcast "Was jetzt" --interval-minutes 30
```

The server stores processed episode IDs in `.pod2text_state.json`.

## Development

```bash
uv run pytest
uv run ruff check .
```

`scripts/setup_env.py` configures `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID`.
Already configured values are automatically skipped, and setup sends a Telegram test message.

## Notes

- The `was jetzt` feed is resolved via an internal catalog entry.
- If you want more podcasts, add entries in `src/pod2text/catalog.py`.
