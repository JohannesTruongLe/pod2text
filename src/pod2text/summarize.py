"""LLM summary generation with chaptered output."""

from __future__ import annotations

from openai import OpenAI

SUMMARY_SYSTEM_PROMPT = """
You summarize podcast transcripts into a concise, easy-to-digest structure.

Return valid Markdown with exactly this structure:

# Episode Summary
## TL;DR
- 3-5 bullets.

## Chapters
### Chapter 1: <short title>
- 2-4 bullets with key points.

### Chapter 2: <short title>
- 2-4 bullets with key points.

Add as many chapters as needed.

## Key Takeaways
- 3-6 practical or memorable points.
""".strip()


def summarize_transcript(transcript: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    if not transcript.strip():
        raise ValueError("Cannot summarize empty transcript.")

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Summarize this podcast transcript into chapters.\n\n"
                    f"Transcript:\n{transcript}"
                ),
            },
        ],
        temperature=0.2,
    )
    summary = response.output_text.strip()
    if not summary:
        raise ValueError("LLM returned an empty summary.")
    return summary
