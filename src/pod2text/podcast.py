"""Feed resolution and latest episode discovery."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import feedparser

from pod2text.catalog import CATALOG


@dataclass(slots=True)
class Episode:
    identifier: str
    title: str
    audio_url: str
    published: str | None = None


def resolve_feed_url(podcast: str) -> str:
    key = podcast.strip().lower()
    if key in CATALOG:
        return CATALOG[key]
    if _looks_like_url(podcast):
        return podcast
    available = ", ".join(sorted(CATALOG))
    raise ValueError(
        f"Unknown podcast '{podcast}'. Use a direct RSS URL or one of: {available}"
    )


def fetch_latest_episode(feed_url: str) -> Episode:
    parsed = feedparser.parse(feed_url)
    if parsed.bozo:
        raise ValueError(f"Failed to parse feed: {feed_url}")

    if not parsed.entries:
        raise ValueError(f"No entries found in feed: {feed_url}")

    first = parsed.entries[0]
    audio_url = _extract_audio_url(first)
    if not audio_url:
        raise ValueError("Latest episode has no downloadable audio enclosure.")

    identifier = (
        _read(first, "id")
        or _read(first, "guid")
        or _read(first, "link")
        or audio_url
    )
    published = _read(first, "published") or None

    return Episode(
        identifier=identifier,
        title=_read(first, "title") or "latest_episode",
        audio_url=audio_url,
        published=published,
    )


def _extract_audio_url(entry: feedparser.FeedParserDict) -> str | None:
    links = getattr(entry, "links", [])
    for link in links:
        rel = _read(link, "rel")
        media_type = _read(link, "type")
        href = _read(link, "href")
        if rel == "enclosure" and media_type.startswith("audio") and href:
            return href
    return None


def _read(value: object, key: str) -> str:
    if isinstance(value, dict):
        return str(value.get(key, ""))
    return str(getattr(value, key, ""))


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
