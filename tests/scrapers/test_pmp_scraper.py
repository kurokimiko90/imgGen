"""tests/scrapers/test_pmp_scraper.py — Unit tests for PMPScraper."""

from unittest.mock import MagicMock, patch

import pytest

from src.scrapers.pmp_scraper import PMPScraper


def make_feed_entry(title="HBR Article", link="http://hbr.org/1", source_tag="hbr"):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.summary = "Management insight"
    entry.published_parsed = (2026, 4, 1, 12, 0, 0, 0, 0, 0)
    entry.get = lambda key, default="": {"summary": "Management insight"}.get(key, default)
    return entry


def make_mock_feed(entries=None):
    feed = MagicMock()
    feed.entries = entries or [make_feed_entry()]
    return feed


class TestPMPScraper:
    def test_fetch_returns_list(self):
        scraper = PMPScraper()
        with patch("feedparser.parse", return_value=make_mock_feed()):
            items = scraper.fetch()
        assert isinstance(items, list)

    def test_hbr_failure_handled(self):
        scraper = PMPScraper()
        call_count = {"n": 0}

        def side_effect(url):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise Exception("HBR down")
            return make_mock_feed([make_feed_entry("PMI Post", "http://pmi.org/1")])

        with patch("feedparser.parse", side_effect=side_effect):
            items = scraper.fetch()
        assert isinstance(items, list)

    def test_pmi_failure_handled(self):
        scraper = PMPScraper()
        call_count = {"n": 0}

        def side_effect(url):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return make_mock_feed()
            raise Exception("PMI down")

        with patch("feedparser.parse", side_effect=side_effect):
            items = scraper.fetch()
        assert isinstance(items, list)

    def test_both_sources_failure_returns_empty(self):
        scraper = PMPScraper()
        with patch("feedparser.parse", side_effect=Exception("all down")):
            items = scraper.fetch()
        assert items == []

    def test_items_have_valid_source(self):
        scraper = PMPScraper()
        with patch("feedparser.parse", return_value=make_mock_feed()):
            items = scraper.fetch()
        if items:
            assert items[0].source in ("hbr", "pmi")
