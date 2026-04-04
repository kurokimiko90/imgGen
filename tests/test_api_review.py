"""
Unit tests for Phase A: Review API helper functions and ContentDAO extensions.

Tests ContentDetail model serialization, database queries, and helper functions
without requiring a full FastAPI TestClient (which has database path issues).
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Ensure modules are importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import ContentDAO
from src.content import Content, ContentStatus, AccountType, ContentType
from src.preflight import preflight_check
from src.scheduler import calculate_scheduled_time


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary test database"""
    db_path = tmp_path / "test_review.db"
    conn = sqlite3.connect(str(db_path))

    # Create schema matching web/api.py expectations
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS generations (
        id INTEGER PRIMARY KEY,
        account_type TEXT DEFAULT 'A',
        status TEXT DEFAULT 'DRAFT',
        content_type TEXT DEFAULT 'NEWS_RECAP',
        title TEXT,
        body TEXT,
        image_path TEXT,
        reasoning TEXT DEFAULT '',
        scheduled_time TEXT,
        published_at TEXT,
        source_url TEXT,
        source TEXT,
        platform_status TEXT DEFAULT '{}',
        engagement_data TEXT DEFAULT '{}',
        created_at TEXT,
        updated_at TEXT
    )
    """)
    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def sample_content(temp_db):
    """Create sample content for testing"""
    dao = ContentDAO(temp_db)

    items = [
        Content(
            id="1",
            account_type=AccountType.A,
            status=ContentStatus.DRAFT,
            content_type=ContentType.NEWS_RECAP,
            title="Draft Item 1",
            body="This is a draft content",
            reasoning="Generated from AI",
            created_at=datetime(2026, 4, 1, 10, 0),
        ),
        Content(
            id="2",
            account_type=AccountType.A,
            status=ContentStatus.PENDING_REVIEW,
            content_type=ContentType.EDUCATIONAL,
            title="Pending Item 2",
            body="Waiting for review",
            reasoning="Manual input",
            created_at=datetime(2026, 4, 2, 10, 0),
        ),
        Content(
            id="3",
            account_type=AccountType.B,
            status=ContentStatus.DRAFT,
            content_type=ContentType.PREDICTION,
            title="Account B Draft",
            body="This is for account B",
            reasoning="Data-driven",
            created_at=datetime(2026, 4, 3, 10, 0),
        ),
    ]

    created_ids = []
    for item in items:
        cid = dao.create(item)
        created_ids.append(cid)

    return created_ids, dao


class TestContentDAOExtensions:
    """Test new ContentDAO methods added for Phase A/B/C/D"""

    def test_find_by_status_single(self, temp_db, sample_content):
        """find_by_status with single ContentStatus"""
        _, dao = sample_content
        results = dao.find_by_status(ContentStatus.DRAFT)
        assert len(results) == 2
        assert all(c.status == ContentStatus.DRAFT for c in results)

    def test_find_by_status_multiple(self, temp_db, sample_content):
        """find_by_status with list of statuses"""
        _, dao = sample_content
        results = dao.find_by_status([ContentStatus.DRAFT, ContentStatus.PENDING_REVIEW])
        assert len(results) == 3
        assert all(c.status in (ContentStatus.DRAFT, ContentStatus.PENDING_REVIEW) for c in results)

    def test_find_by_status_with_account_filter(self, temp_db, sample_content):
        """find_by_status with account_type filter"""
        _, dao = sample_content
        results = dao.find_by_status(ContentStatus.DRAFT, account_type="A")
        assert len(results) == 1
        assert results[0].account_type.value == "A"

    def test_find_scheduled(self, temp_db, sample_content):
        """find_scheduled returns APPROVED content in date range"""
        ids, dao = sample_content
        # Create an APPROVED item with scheduled_time
        content = Content(
            id="test",
            account_type=AccountType.A,
            status=ContentStatus.APPROVED,
            title="Scheduled",
            body="Test",
            scheduled_time=datetime(2026, 4, 5, 10, 0),
        )
        dao.create(content)

        results = dao.find_scheduled("2026-04-05", "2026-04-05", account_type="A")
        assert len(results) == 1
        assert results[0].status == ContentStatus.APPROVED

    def test_find_drafts_basic(self, temp_db, sample_content):
        """find_drafts returns only DRAFT content"""
        _, dao = sample_content
        results = dao.find_drafts()
        assert len(results) == 2
        assert all(c.status == ContentStatus.DRAFT for c in results)

    def test_find_drafts_with_account_filter(self, temp_db, sample_content):
        """find_drafts with account_type filter"""
        _, dao = sample_content
        results = dao.find_drafts(account_type="B")
        assert len(results) == 1
        assert results[0].account_type.value == "B"

    def test_get_curation_stats(self, temp_db, sample_content):
        """get_curation_stats returns account statistics"""
        _, dao = sample_content
        stats = dao.get_curation_stats()
        assert isinstance(stats, dict)


class TestPreflightCheck:
    """Test preflight validation"""

    def test_empty_title_error(self):
        """Preflight should flag empty title as ERROR"""
        content = Content(
            id="1",
            account_type=AccountType.A,
            title="",
            body="Some content"
        )
        warnings = preflight_check(content, [])
        assert any("[ERROR]" in w and "標題" in w for w in warnings)

    def test_empty_body_error(self):
        """Preflight should flag empty body as ERROR"""
        content = Content(
            id="1",
            account_type=AccountType.A,
            title="Title",
            body=""
        )
        warnings = preflight_check(content, [])
        assert any("[ERROR]" in w and "內文" in w for w in warnings)

    def test_instagram_no_image_error(self):
        """Instagram platform requires image"""
        content = Content(
            id="1",
            account_type=AccountType.A,
            title="Title",
            body="Content",
            image_path=None
        )
        warnings = preflight_check(content, ["instagram"])
        assert any("[ERROR]" in w and "IG" in w for w in warnings)

    def test_x_char_limit_warning(self):
        """X platform has 280 char limit"""
        content = Content(
            id="1",
            account_type=AccountType.A,
            title="Title",
            body="x" * 300
        )
        warnings = preflight_check(content, ["x"])
        assert any("[WARNING]" in w and "X" in w for w in warnings)

    def test_clean_content_no_warnings(self):
        """Valid content should have no warnings"""
        content = Content(
            id="1",
            account_type=AccountType.A,
            title="Title",
            body="Content here"
        )
        warnings = preflight_check(content, ["twitter"])
        assert len(warnings) == 0


class TestScheduler:
    """Test scheduling functionality"""

    def test_calculate_scheduled_time_basic(self):
        """Calculate next publish datetime"""
        time = calculate_scheduled_time("09:00")
        assert time.hour == 9
        assert time.minute == 0
        assert time > datetime.now()

    def test_calculate_scheduled_time_invalid_format(self):
        """Invalid publish_time format raises ValueError"""
        with pytest.raises(ValueError):
            calculate_scheduled_time("9:00:00")

    def test_calculate_scheduled_time_invalid_values(self):
        """Invalid hour/minute values raise ValueError"""
        with pytest.raises(ValueError):
            calculate_scheduled_time("25:00")

    def test_calculate_scheduled_time_in_future(self):
        """Scheduled time should always be in the future"""
        time = calculate_scheduled_time("23:00")
        assert time > datetime.now()
