#!/usr/bin/env sh
set -eu

PODCAST="${PODCAST:-Was jetzt}"
INTERVAL_MINUTES="${INTERVAL_MINUTES:-30}"
OUTPUT_DIR="${OUTPUT_DIR:-/app/output}"
STATE_FILE="${STATE_FILE:-/app/output/.pod2text_state.json}"
TRANSCRIPTION_MODEL="${TRANSCRIPTION_MODEL:-small}"
LLM_MODEL="${LLM_MODEL:-gpt-4o-mini}"
LANGUAGE="${LANGUAGE:-de}"

exec uv run pod2text serve \
  --podcast "$PODCAST" \
  --interval-minutes "$INTERVAL_MINUTES" \
  --output-dir "$OUTPUT_DIR" \
  --state-file "$STATE_FILE" \
  --transcription-model "$TRANSCRIPTION_MODEL" \
  --llm-model "$LLM_MODEL" \
  --language "$LANGUAGE"
