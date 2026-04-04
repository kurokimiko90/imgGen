"""
src/scrapers/pmp_scraper.py - Project management / career news scraper.

Sources:
  - Harvard Business Review RSS
  - PMI (Project Management Institute) Blog RSS
"""

from datetime import datetime, timezone

import feedparser

from src.scrapers.base_scraper import BaseScraper, RawItem

HBR_RSS = "https://feeds.hbr.org/harvardbusiness"
PMI_RSS = "https://www.pmi.org/blog/rss"


class PMPScraper(BaseScraper):
    """Scrapes project management and career articles from HBR and PMI."""

    def fetch(self) -> list[RawItem]:
        items: list[RawItem] = []
        items.extend(self._fetch_hbr())
        items.extend(self._fetch_pmi())
        return self.validate_items(items)

    def _fetch_hbr(self) -> list[RawItem]:
        try:
            feed = feedparser.parse(HBR_RSS)
            result = []
            for entry in feed.entries[:8]:
                pub = entry.get("published_parsed")
                published_at = (
                    datetime(*pub[:6], tzinfo=timezone.utc) if pub else datetime.now(timezone.utc)
                )
                result.append(
                    RawItem(
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        summary=entry.get("summary", "")[:300],
                        published_at=published_at,
                        source="hbr",
                    )
                )
            return result
        except Exception as exc:
            print(f"[PMPScraper] HBR RSS error: {exc}")
            return []

    def _fetch_pmi(self) -> list[RawItem]:
        try:
            feed = feedparser.parse(PMI_RSS)
            result = []
            for entry in feed.entries[:8]:
                pub = entry.get("published_parsed")
                published_at = (
                    datetime(*pub[:6], tzinfo=timezone.utc) if pub else datetime.now(timezone.utc)
                )
                result.append(
                    RawItem(
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        summary=entry.get("summary", "")[:300],
                        published_at=published_at,
                        source="pmi",
                    )
                )
            return result
        except Exception as exc:
            print(f"[PMPScraper] PMI RSS error: {exc}")
            return []
