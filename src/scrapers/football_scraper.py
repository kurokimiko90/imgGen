"""
src/scrapers/football_scraper.py - Football news scraper focused on Japanese players in Europe.

兩層架構：
  Layer 1 (CLUB_SOURCES): BBC Sport 各隊 RSS → 全收（有日本選手的俱樂部）
  Layer 2 (GENERAL_SOURCES): 大型媒體 RSS → 姓名 word-boundary フィルタ後収録

日本選手（截至 2025-08）:
  PL:  Mitoma(Brighton), Endo(Liverpool), Tomiyasu(Arsenal), Kamada(Crystal Palace)
  SPL: Furuhashi/Hatate/Maeda/Kobayashi(Celtic)
  BL:  Doan(Freiburg), Ito H(Bayern), Itakura(Gladbach), Asano(Bochum)
  LL:  Kubo(Real Sociedad)
  L1:  Minamino(Monaco), Ito J(Reims), Nakamura(Reims)
  PT:  Morita(Sporting CP)
  ERE: Ueda(Feyenoord), Sugawara(AZ)
  BEL: Machino(Gent)
"""

import re
import os
from datetime import datetime, timedelta, timezone

import feedparser
import httpx

from src.scrapers.base_scraper import BaseScraper, RawItem

# ── 日本選手（英語姓、word-boundary マッチ用）────────────────────────
JAPAN_PLAYERS: dict[str, str] = {
    # Premier League
    "Mitoma":    "Brighton",
    "Endo":      "Liverpool",
    "Tomiyasu":  "Arsenal",
    "Kamada":    "Crystal Palace",
    # Scottish Premiership
    "Furuhashi": "Celtic",
    "Hatate":    "Celtic",
    "Maeda":     "Celtic",
    "Kobayashi": "Celtic",
    # Bundesliga
    "Doan":      "Freiburg",
    "Ito":       "Bayern/Reims",   # Hiroki Ito & Junya Ito 両方
    "Itakura":   "Gladbach",
    "Asano":     "Bochum",
    # La Liga
    "Kubo":      "Real Sociedad",
    # Ligue 1
    "Minamino":  "Monaco",
    "Nakamura":  "Reims",
    # Primeira Liga
    "Morita":    "Sporting",
    # Eredivisie
    "Ueda":      "Feyenoord",
    "Sugawara":  "AZ",
    # Belgian Pro League
    "Machino":   "Gent",
    # 転籍先不明 / 要確認
    "Tanaka":    "",
}

# 単語境界マッチ用パターン（"Ito" が "territory" にマッチしないよう \b を使う）
_JAPAN_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in JAPAN_PLAYERS) + r")\b",
    re.IGNORECASE,
)

# ── Layer 1: BBC Sport 各隊 RSS（有日本選手のクラブ、全収）────────────
CLUB_SOURCES: dict[str, str] = {
    # Premier League
    "bbc_brighton":       "https://feeds.bbci.co.uk/sport/football/teams/brighton-and-hove-albion/rss.xml",
    "bbc_liverpool":      "https://feeds.bbci.co.uk/sport/football/teams/liverpool/rss.xml",
    "bbc_arsenal":        "https://feeds.bbci.co.uk/sport/football/teams/arsenal/rss.xml",
    "bbc_crystal_palace": "https://feeds.bbci.co.uk/sport/football/teams/crystal-palace/rss.xml",
    # Scottish Premiership
    "bbc_celtic":         "https://feeds.bbci.co.uk/sport/football/teams/celtic/rss.xml",
    # Ligue 1
    "bbc_monaco":         "https://feeds.bbci.co.uk/sport/football/teams/monaco/rss.xml",
    # Champions League / Europa (横断的カバー)
    "theguardian_cl":     "https://www.theguardian.com/football/championsleague/rss",
    "theguardian_transfers": "https://www.theguardian.com/football/transfers/rss",
}

# ── Layer 2: 大型メディア RSS（姓フィルタ後）────────────────────────
GENERAL_SOURCES: dict[str, str] = {
    "bbc_sport":              "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "espn_fc":                "https://www.espn.com/espn/rss/soccer/news",
    "sky_sports":             "https://www.skysports.com/rss/12040",
    "fourfourtwo":            "https://www.fourfourtwo.com/rss",
    "theguardian_football":   "https://www.theguardian.com/football/rss",
}

MAX_PER_CLUB    = 10
MAX_PER_GENERAL = 20   # 多く取ってフィルタ

API_FOOTBALL_BASE = "https://api-football-v1.p.rapidapi.com/v3"

_HTML_TAG  = re.compile(r"<[^>]+>")
_MULTISPACE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    return _MULTISPACE.sub(" ", _HTML_TAG.sub(" ", text)).strip()


def _is_japan_related(item: RawItem) -> bool:
    """タイトル＋サマリーに日本選手の姓（単語境界）が含まれるか判定。"""
    return bool(_JAPAN_PATTERN.search(item.title + " " + item.summary))


class FootballScraper(BaseScraper):
    """
    Layer 1: 俱樂部 BBC RSS → 全收
    Layer 2: 大型メディア RSS → 姓キーワードフィルタ後収録
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")

    def fetch(self) -> list[RawItem]:
        seen_urls: set[str] = set()
        items: list[RawItem] = []

        for name, url in CLUB_SOURCES.items():
            items.extend(self._fetch_rss(name, url, seen_urls, MAX_PER_CLUB, filter_japan=False))

        for name, url in GENERAL_SOURCES.items():
            items.extend(self._fetch_rss(name, url, seen_urls, MAX_PER_GENERAL, filter_japan=True))

        if self.api_key:
            items.extend(self._fetch_api_football())

        validated = self.validate_items(items)
        japan_count = sum(1 for i in validated if _is_japan_related(i))
        print(f"[FootballScraper] total={len(validated)}, japan_related={japan_count}")
        return validated

    def _fetch_rss(
        self,
        source_name: str,
        feed_url: str,
        seen_urls: set[str],
        limit: int,
        filter_japan: bool,
    ) -> list[RawItem]:
        try:
            feed = feedparser.parse(feed_url, agent="Mozilla/5.0 (compatible; feedparser/6.0)")

            if feed.bozo and not feed.entries:
                print(f"[FootballScraper] {source_name}: skipped (parse error)")
                return []

            result = []
            for entry in feed.entries[:limit]:
                link = entry.get("link", "")
                if not link or link in seen_urls:
                    continue

                pub = entry.get("published_parsed")
                published_at = (
                    datetime(*pub[:6], tzinfo=timezone.utc) if pub else datetime.now(timezone.utc)
                )

                content = ""
                if entry.get("content"):
                    content = entry["content"][0].get("value", "")
                if not content:
                    content = entry.get("summary", "")
                content = _strip_html(content)[:800]

                item = RawItem(
                    title=entry.get("title", ""),
                    url=link,
                    summary=content,
                    published_at=published_at,
                    source=source_name,
                )

                if filter_japan and not _is_japan_related(item):
                    continue

                seen_urls.add(link)
                result.append(item)

            print(f"[FootballScraper] {source_name}: {len(result)} items")
            return result

        except Exception as exc:
            print(f"[FootballScraper] {source_name} error: {exc}")
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
