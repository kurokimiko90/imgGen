"""
src/scrapers/pmp_scraper.py - Project management / career news scraper.

Sources:
  - Rebel's Guide to PM (Elizabeth Harrin) — practitioner blog, top PM authority
  - Online PM Courses (Mike Clayton) — educator, 10 PM books author
  - Fast Company Leadership — workplace / career / leadership
  - Agile Alliance Blog — agile / scrum / project delivery
  - HBR Managing People — Harvard Business Review (topic-filtered)
  - HBR Leadership — Harvard Business Review leadership
"""

from datetime import datetime, timezone

import feedparser

from src.scrapers.base_scraper import BaseScraper, RawItem

SOURCES = {
    "rebel_pm": "https://rebelsguidetopm.com/feed/",
    "online_pm_courses": "https://onlinepmcourses.com/feed/",
    "fastcompany_leadership": "https://www.fastcompany.com/work-life/rss",
    "agile_alliance": "https://www.agilealliance.org/feed/",
    "hbr_management": "https://hbr.org/topic/subject/managing-people/feed",
    "hbr_leadership": "https://hbr.org/topic/subject/leadership/feed",
}

MAX_PER_SOURCE = 6


class PMPScraper(BaseScraper):
    """Scrapes project management and career content from authority sources."""

    def fetch(self) -> list[RawItem]:
        items: list[RawItem] = []
        for source_id, url in SOURCES.items():
            items.extend(self._fetch_feed(source_id, url))
        return self.validate_items(items)

    def _fetch_feed(self, source_id: str, url: str) -> list[RawItem]:
        try:
            feed = feedparser.parse(url)
            result = []
            for entry in feed.entries[:MAX_PER_SOURCE]:
                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                published_at = (
                    datetime(*pub[:6], tzinfo=timezone.utc)
                    if pub
                    else datetime.now(timezone.utc)
                )
                summary = (
                    entry.get("summary", "")
                    or entry.get("description", "")
                    or ""
                )
                result.append(
                    RawItem(
                        title=entry.get("title", "").strip(),
                        url=entry.get("link", ""),
                        summary=summary[:400],
                        published_at=published_at,
                        source=source_id,
                    )
                )
            return result
        except Exception as exc:
            print(f"[PMPScraper] {source_id} error: {exc}")
            return []
