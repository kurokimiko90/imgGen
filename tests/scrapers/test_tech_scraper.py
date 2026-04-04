"""tests/scrapers/test_tech_scraper.py — Unit tests for TechScraper."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.scrapers.base_scraper import RawItem
from src.scrapers.tech_scraper import TechScraper


def make_hn_response(story_ids=None):
    mock = MagicMock()
    mock.json.return_value = story_ids or [1, 2, 3]
    mock.raise_for_status = MagicMock()
    return mock


def make_hn_item(story_id=1, title="HN Title", url="http://example.com"):
    mock = MagicMock()
    mock.json.return_value = {
        "id": story_id,
        "type": "story",
        "title": title,
        "url": url,
        "time": 1743772800,
    }
    mock.raise_for_status = MagicMock()
    return mock


def make_tc_feed_entry(title="TC Title", link="http://techcrunch.com/1"):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.summary = "TC summary"
    entry.published_parsed = (2026, 4, 1, 12, 0, 0, 0, 0, 0)
    entry.get = lambda key, default="": {"summary": "TC summary", "title": title, "link": link}.get(key, default)
    return entry


class TestTechScraper:
    def test_fetch_returns_list(self):
        scraper = TechScraper()
        with (
            patch("httpx.get", side_effect=Exception("network")),
            patch("feedparser.parse", side_effect=Exception("rss")),
        ):
            items = scraper.fetch()
        assert isinstance(items, list)
        assert items == []

    def test_hacker_news_failure_handled(self):
        scraper = TechScraper()
        with (
            patch("httpx.get", side_effect=Exception("HN down")),
            patch("feedparser.parse", return_value=MagicMock(entries=[])),
        ):
            items = scraper.fetch()
        assert items == []

    def test_techcrunch_failure_does_not_block_hn(self):
        scraper = TechScraper()
        tc_item = make_hn_item(title="HN Story", url="http://hn.com/1")

        with (
            patch("httpx.get", side_effect=[make_hn_response([1]), tc_item]),
            patch("feedparser.parse", side_effect=Exception("TC down")),
        ):
            items = scraper.fetch()
        assert isinstance(items, list)

    def test_item_source_is_hacker_news(self):
        scraper = TechScraper()
        top_resp = make_hn_response([42])
        item_resp = make_hn_item(story_id=42, title="AI News", url="http://ai.com")

        tc_feed = MagicMock()
        tc_feed.entries = []

        with (
            patch("httpx.get", side_effect=[top_resp, item_resp]),
            patch("feedparser.parse", return_value=tc_feed),
        ):
            items = scraper.fetch()

        assert any(i.source == "hacker_news" for i in items)

    def test_techcrunch_items_have_correct_source(self):
        scraper = TechScraper()
        tc_feed = MagicMock()
        tc_feed.entries = [make_tc_feed_entry()]

        with (
            patch("httpx.get", side_effect=Exception("HN down")),
            patch("feedparser.parse", return_value=tc_feed),
        ):
            items = scraper.fetch()

        if items:
            assert items[0].source == "techcrunch"
