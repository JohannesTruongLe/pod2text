from __future__ import annotations

import pytest

from pod2text.podcast import fetch_latest_episode, resolve_feed_url


def test_resolve_feed_url_with_catalog_name() -> None:
    assert resolve_feed_url("Was Jetzt") == "https://feeds.simplecast.com/Xtqjn37O"


def test_resolve_feed_url_with_direct_url() -> None:
    url = "https://example.com/feed.xml"
    assert resolve_feed_url(url) == url


def test_resolve_feed_url_unknown_podcast() -> None:
    with pytest.raises(ValueError):
        resolve_feed_url("unknown-show")


def test_fetch_latest_episode(monkeypatch: pytest.MonkeyPatch) -> None:
    class Entry:
        title = "Episode 1"
        published = "today"
        links = [
            {
                "rel": "enclosure",
                "type": "audio/mpeg",
                "href": "https://cdn.example.com/ep1.mp3",
            }
        ]

    class Parsed:
        bozo = False
        entries = [Entry()]

    monkeypatch.setattr("pod2text.podcast.feedparser.parse", lambda _: Parsed())

    episode = fetch_latest_episode("https://example.com/feed.xml")
    assert episode.identifier == "https://cdn.example.com/ep1.mp3"
    assert episode.title == "Episode 1"
    assert episode.audio_url == "https://cdn.example.com/ep1.mp3"
