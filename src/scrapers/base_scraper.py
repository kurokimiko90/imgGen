"""
src/scrapers/base_scraper.py - Abstract base class for all content scrapers.

Defines the common interface and RawItem data format used by all scrapers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawItem:
    """Universal raw content item from any scraper source."""

    title: str
    url: str
    summary: str
    published_at: datetime
    source: str  # e.g. "hacker_news" | "bbc_sport" | "techcrunch" | "hbr"


class BaseScraper(ABC):
    """Abstract base class for all content scrapers."""

    @abstractmethod
    def fetch(self) -> list[RawItem]:
        """Fetch latest content items from the source.

        Subclasses must implement this. Should never raise — catch all
        exceptions internally and return an empty list on failure.
        """

    def validate_items(self, items: list[RawItem]) -> list[RawItem]:
        """Filter out incomplete RawItems (missing title, url, or published_at)."""
        return [
            item for item in items
            if item.title and item.url and item.published_at
        ]
