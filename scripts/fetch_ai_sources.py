"""
scripts/fetch_ai_sources.py — Test AI content sources independently.

Usage:
    python scripts/fetch_ai_sources.py                # fetch all sources
    python scripts/fetch_ai_sources.py --source openai_blog
    python scripts/fetch_ai_sources.py --no-arxiv     # skip arxiv
    python scripts/fetch_ai_sources.py --no-reddit    # skip reddit
    python scripts/fetch_ai_sources.py --json         # output as JSON
"""

import json
import sys
from pathlib import Path

import click

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapers.ai_scraper import (
    AIScraper,
    RSS_SOURCES,
    LEADER_RSS_SOURCES,
    REDDIT_SUBS,
)


@click.command()
@click.option("--source", default=None, help="Only fetch from this source name")
@click.option("--no-arxiv", is_flag=True, help="Skip arXiv")
@click.option("--no-reddit", is_flag=True, help="Skip Reddit")
@click.option("--json-out", "as_json", is_flag=True, help="Output as JSON")
def main(source, no_arxiv, no_reddit, as_json):
    """Fetch and display AI content from all configured sources."""

    if source:
        # Single source mode
        scraper = AIScraper(include_arxiv=False, include_reddit=False)
        all_sources = {**RSS_SOURCES, **LEADER_RSS_SOURCES}
        if source not in all_sources and source not in [f"reddit_{s.lower()}" for s in REDDIT_SUBS] and source != "arxiv":
            print(f"Unknown source: {source}")
            print(f"Available: {', '.join(sorted(all_sources.keys()))} + reddit_* + arxiv")
            return

        if source in all_sources:
            items = scraper._fetch_rss(all_sources[source], source)
        elif source == "arxiv":
            items = scraper._fetch_arxiv()
        elif source.startswith("reddit_"):
            sub = source.replace("reddit_", "")
            items = scraper._fetch_reddit(sub)
        else:
            items = []
    else:
        # Full fetch
        scraper = AIScraper(
            include_arxiv=not no_arxiv,
            include_reddit=not no_reddit,
        )
        items = scraper.fetch()

    if as_json:
        data = [
            {
                "title": item.title,
                "url": item.url,
                "summary": item.summary[:200],
                "published_at": item.published_at.isoformat(),
                "source": item.source,
            }
            for item in items
        ]
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # Pretty print
    by_source: dict[str, list] = {}
    for item in items:
        by_source.setdefault(item.source, []).append(item)

    total = len(items)
    print(f"\n{'='*60}")
    print(f"  AI Content Sources — {total} items from {len(by_source)} sources")
    print(f"{'='*60}\n")

    for src, src_items in sorted(by_source.items()):
        print(f"📡 {src} ({len(src_items)} items)")
        print(f"{'─'*50}")
        for item in src_items:
            age = _format_age(item.published_at)
            print(f"  [{age}] {item.title[:70]}")
            if item.summary:
                print(f"         {item.summary[:100]}...")
            print(f"         {item.url}")
        print()

    # Summary
    print(f"{'='*60}")
    print(f"  Summary: {total} items | {len(by_source)} sources")
    tier1 = sum(len(v) for k, v in by_source.items() if k in RSS_SOURCES or k.startswith("reddit_") or k == "arxiv")
    tier2 = sum(len(v) for k, v in by_source.items() if k in LEADER_RSS_SOURCES)
    print(f"  Tier 1 (companies/communities): {tier1}")
    print(f"  Tier 2 (thought leaders): {tier2}")
    print(f"{'='*60}\n")


def _format_age(dt) -> str:
    """Format a datetime as a human-readable age string."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    delta = now - dt
    if delta.days > 30:
        return f"{delta.days // 30}mo"
    elif delta.days > 0:
        return f"{delta.days}d"
    elif delta.seconds > 3600:
        return f"{delta.seconds // 3600}h"
    else:
        return f"{delta.seconds // 60}m"


if __name__ == "__main__":
    main()
