"""tests/scrapers/test_football_scraper.py — Unit tests for FootballScraper."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.scrapers.base_scraper import RawItem
from src.scrapers.football_scraper import FootballScraper


def make_feed_entry(title="Match Report", link="http://bbc.co.uk/1"):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.summary = "Summary text"
    entry.published_parsed = (2026, 4, 1, 12, 0, 0, 0, 0, 0)
    entry.get = lambda key, default="": {"summary": "Summary text", "title": title, "link": link}.get(key, default)
    return entry


def make_mock_feed(entries=None):
    feed = MagicMock()
    feed.entries = entries or [make_feed_entry()]
    return feed


class TestFootballScraper:
    def test_fetch_returns_list(self):
        scraper = FootballScraper(api_key=None)
        with patch("feedparser.parse", return_value=make_mock_feed()):
            items = scraper.fetch()
        assert isinstance(items, list)

    def test_fetch_returns_raw_items(self):
        scraper = FootballScraper(api_key=None)
        with patch("feedparser.parse", return_value=make_mock_feed()):
            items = scraper.fetch()
        assert all(isinstance(i, RawItem) for i in items)

    def test_rss_parsing_failure_handled(self):
        scraper = FootballScraper(api_key=None)
        with patch("feedparser.parse", side_effect=Exception("Network error")):
            items = scraper.fetch()
        assert items == []

    def test_raw_item_has_source_bbc_sport(self):
        scraper = FootballScraper(api_key=None)
        with patch("feedparser.parse", return_value=make_mock_feed()):
            items = scraper.fetch()
        if items:
            assert items[0].source == "bbc_sport"

    def test_validate_items_filters_empty_title(self):
        scraper = FootballScraper(api_key=None)
        items = [
            RawItem(title="Valid", url="http://a.com", summary="", published_at=datetime.now(timezone.utc), source="test"),
            RawItem(title="", url="http://b.com", summary="", published_at=datetime.now(timezone.utc), source="test"),
        ]
        valid = scraper.validate_items(items)
        assert len(valid) == 1
        assert valid[0].title == "Valid"

    def test_validate_items_filters_empty_url(self):
        scraper = FootballScraper(api_key=None)
        items = [
            RawItem(title="Title", url="", summary="", published_at=datetime.now(timezone.utc), source="test"),
        ]
        assert scraper.validate_items(items) == []
