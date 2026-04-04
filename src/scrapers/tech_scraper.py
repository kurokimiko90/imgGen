"""
src/scrapers/tech_scraper.py - Technology news scraper.

Sources:
  - Hacker News API (public, no key required)
  - TechCrunch RSS
"""

from datetime import datetime, timezone

import feedparser
import httpx

from src.scrapers.base_scraper import BaseScraper, RawItem

HN_TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
TECHCRUNCH_RSS = "https://techcrunch.com/feed/"

_HN_FETCH_LIMIT = 30
_HN_ITEM_LIMIT = 10


class TechScraper(BaseScraper):
    """Scrapes tech news from Hacker News and TechCrunch RSS."""

    def fetch(self) -> list[RawItem]:
        items: list[RawItem] = []
        items.extend(self._fetch_hacker_news())
        items.extend(self._fetch_techcrunch())
        return self.validate_items(items)

    def _fetch_hacker_news(self) -> list[RawItem]:
        try:
            resp = httpx.get(HN_TOP_STORIES, timeout=10)
            resp.raise_for_status()
            story_ids = resp.json()[:_HN_FETCH_LIMIT]
        except Exception as exc:
            print(f"[TechScraper] HN top stories error: {exc}")
            return []

        items: list[RawItem] = []
        for story_id in story_ids[:_HN_ITEM_LIMIT]:
            try:
                r = httpx.get(HN_ITEM_URL.format(story_id), timeout=10)
                r.raise_for_status()
                data = r.json()
                if not data or data.get("type") != "story":
                    continue
                items.append(
                    RawItem(
                        title=data.get("title", ""),
                        url=data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        summary="",
                        published_at=datetime.fromtimestamp(
                            data.get("time", 0), tz=timezone.utc
                        ),
                        source="hacker_news",
                    )
                )
            except Exception as exc:
                print(f"[TechScraper] HN item {story_id} error: {exc}")
        return items

    def _fetch_techcrunch(self) -> list[RawItem]:
        try:
            feed = feedparser.parse(TECHCRUNCH_RSS)
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
                        source="techcrunch",
                    )
                )
            return result
        except Exception as exc:
            print(f"[TechScraper] TechCrunch RSS error: {exc}")
            return []
