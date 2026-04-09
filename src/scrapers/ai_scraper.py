"""
src/scrapers/ai_scraper.py - AI-focused content scraper.

Sources (all free, no API key required):
  Tier 1 — Company blogs & communities:
    - OpenAI Blog RSS
    - Google AI Blog RSS
    - Facebook/Meta Engineering RSS
    - HuggingFace Blog RSS
    - Import AI Newsletter (Substack)
    - The Batch / Andrew Ng (deeplearning.ai)
    - arXiv cs.AI/cs.CL/cs.LG (API)
    - r/MachineLearning (Reddit JSON)
    - r/LocalLLaMA (Reddit JSON)

  Tier 2 — AI thought leaders:
    - Andrej Karpathy (YouTube RSS)
    - AI Snake Oil / Arvind Narayanan (Substack)
    - Simon Willison (Blog RSS)
    - Lilian Weng (Blog RSS)
    - Latent Space / Swyx (Podcast RSS)
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Optional

import feedparser
import httpx

from src.scrapers.base_scraper import BaseScraper, RawItem

# ---------------------------------------------------------------------------
# Tier 1: Company blogs & communities
# ---------------------------------------------------------------------------

RSS_SOURCES: dict[str, str] = {
    "openai_blog": "https://openai.com/blog/rss.xml",
    "google_ai_blog": "https://blog.google/technology/ai/rss/",
    "fb_engineering": "https://engineering.fb.com/feed/",  # Meta/Facebook AI eng
    "huggingface_blog": "https://huggingface.co/blog/feed.xml",
    "import_ai": "https://importai.substack.com/feed",
    "the_batch": "https://www.deeplearning.ai/the-batch/feed.xml",  # Andrew Ng's newsletter
}

# ---------------------------------------------------------------------------
# Tier 2: AI thought leaders
# ---------------------------------------------------------------------------

LEADER_RSS_SOURCES: dict[str, str] = {
    # Andrej Karpathy YouTube channel RSS
    "karpathy_youtube": "https://www.youtube.com/feeds/videos.xml?channel_id=UCXUPKJO5MZQN11PqgIvyuvQ",
    # AI Snake Oil — academic AI criticism (Arvind Narayanan, Princeton)
    "ai_snake_oil": "https://www.aisnakeoil.com/feed",
    # Simon Willison
    "simon_willison": "https://simonwillison.net/atom/everything/",
    # Lilian Weng
    "lilian_weng": "https://lilianweng.github.io/index.xml",
    # Latent Space podcast
    "latent_space": "https://api.substack.com/feed/podcast/1084089/s/89848.rss",
}

# Reddit subreddits (JSON API, no auth needed)
REDDIT_SUBS: list[str] = ["MachineLearning", "LocalLLaMA"]

# arXiv categories
ARXIV_CATEGORIES: list[str] = ["cs.AI", "cs.CL", "cs.LG"]

# Max items per source to prevent flood
_PER_SOURCE_LIMIT = 8
_REDDIT_LIMIT = 10
_ARXIV_LIMIT = 10

# HTTP timeout
_TIMEOUT = 15

# User-Agent for Reddit (required by their API)
_HEADERS = {
    "User-Agent": "imgGen-ai-scraper/1.0 (content curation bot)"
}


def _parse_rss_date(entry: dict) -> datetime:
    """Extract published date from a feedparser entry."""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
    return datetime.now(timezone.utc)


def _clean_html(text: str) -> str:
    """Strip HTML tags from summary text."""
    clean = re.sub(r"<[^>]+>", "", text or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:400]


class AIScraper(BaseScraper):
    """Scrapes AI-specific content from blogs, Reddit, arXiv, and KOL feeds."""

    def __init__(self, include_arxiv: bool = True, include_reddit: bool = True):
        self.include_arxiv = include_arxiv
        self.include_reddit = include_reddit

    def fetch(self) -> list[RawItem]:
        items: list[RawItem] = []

        # Tier 1: Company blogs
        for source_name, url in RSS_SOURCES.items():
            items.extend(self._fetch_rss(url, source_name))

        # Tier 2: Leader feeds
        for source_name, url in LEADER_RSS_SOURCES.items():
            items.extend(self._fetch_rss(url, source_name))

        # Reddit
        if self.include_reddit:
            for sub in REDDIT_SUBS:
                items.extend(self._fetch_reddit(sub))

        # arXiv
        if self.include_arxiv:
            items.extend(self._fetch_arxiv())

        # Deduplicate by URL
        seen_urls: set[str] = set()
        deduped: list[RawItem] = []
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                deduped.append(item)

        # Sort by published_at descending (newest first)
        deduped.sort(key=lambda x: x.published_at, reverse=True)

        return self.validate_items(deduped)

    def _fetch_rss(self, url: str, source_name: str) -> list[RawItem]:
        """Fetch items from an RSS/Atom feed."""
        try:
            # feedparser can handle URLs directly but httpx gives us timeout control
            resp = httpx.get(url, timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

            items: list[RawItem] = []
            for entry in feed.entries[:_PER_SOURCE_LIMIT]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = _clean_html(
                    entry.get("summary", "") or entry.get("description", "")
                )
                published_at = _parse_rss_date(entry)

                if title and link:
                    items.append(RawItem(
                        title=title,
                        url=link,
                        summary=summary,
                        published_at=published_at,
                        source=source_name,
                    ))
            return items

        except Exception as exc:
            print(f"[AIScraper] {source_name} error: {exc}")
            return []

    def _fetch_reddit(self, subreddit: str) -> list[RawItem]:
        """Fetch hot posts from a subreddit via JSON API (no auth)."""
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={_REDDIT_LIMIT}"
        try:
            resp = httpx.get(url, timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()

            items: list[RawItem] = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                if post.get("stickied"):
                    continue

                title = post.get("title", "")
                permalink = post.get("permalink", "")
                selftext = (post.get("selftext") or "")[:300]
                created_utc = post.get("created_utc", 0)

                link = post.get("url", f"https://reddit.com{permalink}")
                # If the post links to reddit itself, use permalink
                if "reddit.com" in link and "/comments/" in link:
                    link = f"https://reddit.com{permalink}"

                items.append(RawItem(
                    title=title,
                    url=link,
                    summary=selftext,
                    published_at=datetime.fromtimestamp(created_utc, tz=timezone.utc),
                    source=f"reddit_{subreddit.lower()}",
                ))
            return items

        except Exception as exc:
            print(f"[AIScraper] r/{subreddit} error: {exc}")
            return []

    def _fetch_arxiv(self) -> list[RawItem]:
        """Fetch recent AI papers from arXiv API."""
        cats = "+OR+".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
        url = (
            f"http://export.arxiv.org/api/query?"
            f"search_query={cats}&sortBy=submittedDate&sortOrder=descending"
            f"&start=0&max_results={_ARXIV_LIMIT}"
        )
        try:
            resp = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True)
            resp.raise_for_status()

            # Parse Atom XML
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            items: list[RawItem] = []
            for entry in root.findall("atom:entry", ns):
                title_el = entry.find("atom:title", ns)
                summary_el = entry.find("atom:summary", ns)
                published_el = entry.find("atom:published", ns)
                link_el = entry.find("atom:id", ns)

                title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
                summary = _clean_html(summary_el.text if summary_el is not None else "")
                link = (link_el.text or "").strip() if link_el is not None else ""
                # Convert arXiv abs URL to a cleaner format
                link = link.replace("http://", "https://")

                published_at = datetime.now(timezone.utc)
                if published_el is not None and published_el.text:
                    try:
                        published_at = datetime.fromisoformat(
                            published_el.text.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                if title and link:
                    items.append(RawItem(
                        title=title,
                        url=link,
                        summary=summary,
                        published_at=published_at,
                        source="arxiv",
                    ))
            return items

        except Exception as exc:
            print(f"[AIScraper] arXiv error: {exc}")
            return []
