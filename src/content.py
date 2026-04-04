"""
src/content.py - Content data model and state machine for LevelUp system.

Defines the Content dataclass, status/type enumerations, and the
VALID_TRANSITIONS table that enforces the content workflow:
    DRAFT -> PENDING_REVIEW -> APPROVED -> PUBLISHED -> ANALYZED
    DRAFT -> REJECTED
    PENDING_REVIEW -> REJECTED
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from enum import Enum
import json


class ContentStatus(str, Enum):
    DRAFT = 'DRAFT'
    PENDING_REVIEW = 'PENDING_REVIEW'
    APPROVED = 'APPROVED'
    PUBLISHED = 'PUBLISHED'
    ANALYZED = 'ANALYZED'
    REJECTED = 'REJECTED'


class ContentType(str, Enum):
    NEWS_RECAP = 'NEWS_RECAP'
    PREDICTION = 'PREDICTION'
    EDUCATIONAL = 'EDUCATIONAL'


class AccountType(str, Enum):
    A = 'A'  # AI automation
    B = 'B'  # PMP career
    C = 'C'  # Soccer English


# Valid state transitions: maps current status -> set of allowed next statuses
VALID_TRANSITIONS: dict[ContentStatus, set[ContentStatus]] = {
    ContentStatus.DRAFT: {ContentStatus.PENDING_REVIEW, ContentStatus.REJECTED},
    ContentStatus.PENDING_REVIEW: {ContentStatus.APPROVED, ContentStatus.REJECTED},
    ContentStatus.APPROVED: {ContentStatus.PUBLISHED},
    ContentStatus.PUBLISHED: {ContentStatus.ANALYZED},
}


class InvalidTransitionError(Exception):
    """Raised when a state transition is not permitted by the state machine."""
    pass


@dataclass
class Content:
    """Represents a piece of managed content in the LevelUp pipeline."""

    id: str
    account_type: AccountType
    status: ContentStatus = ContentStatus.DRAFT
    content_type: ContentType = ContentType.NEWS_RECAP
    title: str = ""
    body: str = ""
    image_path: Optional[str] = None
    reasoning: str = ""
    scheduled_time: Optional[datetime] = None
    published_at: Optional[datetime] = None
    source_url: Optional[str] = None
    source: Optional[str] = None  # e.g. "hacker_news", "techcrunch"
    platform_status: dict = field(default_factory=dict)
    engagement_data: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def transition_to(self, new_status: ContentStatus) -> None:
        """Validate and apply a state transition.

        Args:
            new_status: The target status to transition to.

        Raises:
            InvalidTransitionError: If the transition is not permitted.
        """
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Serialize to dict, converting datetime and Enum to JSON-safe types."""
        data = asdict(self)
        data['status'] = self.status.value
        data['account_type'] = self.account_type.value
        data['content_type'] = self.content_type.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        data['scheduled_time'] = self.scheduled_time.isoformat() if self.scheduled_time else None
        data['published_at'] = self.published_at.isoformat() if self.published_at else None
        return data

    @staticmethod
    def from_dict(data: dict) -> 'Content':
        """Deserialize from dict, converting strings back to Enums and datetimes.

        Args:
            data: Dict representation, typically from to_dict() or a DB row.

        Returns:
            A new Content instance with all fields populated.
        """
        data = data.copy()

        # Convert string values to Enums
        if isinstance(data.get('status'), str):
            data['status'] = ContentStatus(data['status'])
        if isinstance(data.get('account_type'), str):
            data['account_type'] = AccountType(data['account_type'])
        if isinstance(data.get('content_type'), str):
            data['content_type'] = ContentType(data['content_type'])

        # Convert ISO strings to datetime
        for field_name in ['created_at', 'updated_at', 'scheduled_time', 'published_at']:
            if data.get(field_name) and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])

        return Content(**data)
