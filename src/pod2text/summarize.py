"""LLM summary generation with chaptered output."""

from __future__ import annotations

from openai import OpenAI

SUMMARY_SYSTEM_PROMPT = """
You summarize podcast transcripts into a clear, detailed-but-concise structure.

Write in a journalistic, readable style. The goal is not maximum compression, but a high-signal summary that preserves important details.

Return valid Markdown with EXACTLY this structure:

# Episode Summary

## TL;DR
- 3-5 bullets.
- Each bullet should be 1–2 sentences and include concrete details (who/what/why).
- Prefer specifics over vague wording (include names, numbers, places, dates when available).

## Chapters
Split the episode into logical sections in chronological order.

For each chapter:
- Use a short descriptive title (max 6 words).
- Provide 3-5 bullets per chapter.
- Each bullet should contain a complete idea (1–2 sentences).
- Include key facts, arguments, examples, and important quotes (paraphrased).
- Highlight major numbers, events, and claims.

### Chapter 1: <short title>
- ...

### Chapter 2: <short title>
- ...

Add as many chapters as needed.

## Key Takeaways
- 4-7 bullets.
- Focus on practical, memorable insights.
- Phrase them as actionable lessons or "what this means".
- Use **bold** emphasis sparingly to highlight key concepts or names.

Style rules:
- Keep language clean and readable.
- Avoid filler phrases like "the hosts discuss" unless necessary.
- Avoid overly generic bullets.
- Prefer clarity over cleverness.
- Use Markdown formatting to make it Telegram-friendly (short bullets, good spacing, occasional **bold** emphasis).
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
