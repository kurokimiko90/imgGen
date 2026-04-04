"""
src/scrapers/football_scraper.py - Football news scraper.

Sources:
  - BBC Sport Football RSS (no key required)
  - API-Football via RapidAPI (optional, requires API_FOOTBALL_KEY env var)
"""

import os
from datetime import datetime, timedelta, timezone

import feedparser
import httpx

from src.scrapers.base_scraper import BaseScraper, RawItem

BBC_SPORT_RSS = "https://feeds.bbci.co.uk/sport/football/rss.xml"
API_FOOTBALL_BASE = "https://api-football-v1.p.rapidapi.com/v3"


class FootballScraper(BaseScraper):
    """Scrapes football news from BBC Sport RSS and optionally API-Football."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")

    def fetch(self) -> list[RawItem]:
        items: list[RawItem] = []
        items.extend(self._fetch_bbc_rss())
        if self.api_key:
            items.extend(self._fetch_api_football())
        return self.validate_items(items)

    def _fetch_bbc_rss(self) -> list[RawItem]:
        try:
            feed = feedparser.parse(BBC_SPORT_RSS)
            result = []
            for entry in feed.entries[:10]:
                pub = entry.get("published_parsed")
                published_at = (
                    datetime(*pub[:6], tzinfo=timezone.utc) if pub else datetime.now(timezone.utc)
                )
                result.append(
                    RawItem(
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        summary=entry.get("summary", ""),
                        published_at=published_at,
                        source="bbc_sport",
                    )
                )
            return result
        except Exception as exc:
            print(f"[FootballScraper] BBC RSS error: {exc}")
            return []

    def _fetch_api_football(self) -> list[RawItem]:
        items: list[RawItem] = []
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
        }
        for days_ahead in range(3):
            date_str = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            try:
                resp = httpx.get(
                    f"{API_FOOTBALL_BASE}/fixtures",
                    params={"date": date_str, "league": "39", "season": "2024"},
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
                for fixture in resp.json().get("response", [])[:5]:
                    teams = fixture.get("teams", {})
                    home = teams.get("home", {}).get("name", "")
                    away = teams.get("away", {}).get("name", "")
                    title = f"{home} vs {away} — {date_str}"
                    items.append(
                        RawItem(
                            title=title,
                            url=f"https://www.api-football.com/fixture/{fixture['fixture']['id']}",
                            summary=f"Kickoff: {fixture['fixture'].get('date', '')}",
                            published_at=datetime.now(timezone.utc),
                            source="api_football",
                        )
                    )
            except Exception as exc:
                print(f"[FootballScraper] API-Football error ({date_str}): {exc}")
        return items
