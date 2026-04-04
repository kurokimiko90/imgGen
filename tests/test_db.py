import pytest
import sqlite3
from pathlib import Path
from src.db import ContentDAO
from src.content import Content, ContentStatus, AccountType, ContentType


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary test database with full schema"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))

    # Create schema with all columns (post-migration)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE generations (
        id INTEGER PRIMARY KEY,
        account_type TEXT DEFAULT 'A',
        status TEXT DEFAULT 'DRAFT',
        content_type TEXT DEFAULT 'NEWS_RECAP',
        title TEXT,
        body TEXT,
        image_path TEXT,
        output_path TEXT,
        reasoning TEXT DEFAULT '',
        scheduled_time TEXT,
        published_at TEXT,
        source_url TEXT,
        source TEXT,
        provider TEXT DEFAULT 'cli',
        theme TEXT,
        format TEXT,
        platform_status TEXT DEFAULT '{}',
        engagement_data TEXT DEFAULT '{}',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        key_points_count INTEGER
    )
    """)
    # Create migrations table and mark all migrations as applied
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS _migrations (
        name TEXT PRIMARY KEY,
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # Mark all migrations as applied so DAO doesn't try to re-apply them
    migration_files = ["000_create_generations_table.sql", "001_add_levelup_columns.sql",
                      "002_add_body_column.sql", "003_add_image_path_column.sql",
                      "004_add_updated_at_column.sql"]
    for migration_file in migration_files:
        cursor.execute("INSERT OR IGNORE INTO _migrations (name) VALUES (?)", (migration_file,))
    conn.commit()
    conn.close()
    return str(db_path)


class TestContentDAO:
    def test_create_inserts_content(self, temp_db):
        """create() should insert and return id"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.A, title="Test", body="Body")
        content_id = dao.create(c)
        assert content_id is not None

    def test_find_by_id_retrieves_content(self, temp_db):
        """find_by_id() should retrieve inserted content"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.B, title="Test", body="Body")
        content_id = dao.create(c)

        retrieved = dao.find_by_id(content_id)
        assert retrieved is not None
        assert retrieved.title == "Test"
        assert retrieved.account_type == AccountType.B

    def test_find_by_status_filters_correctly(self, temp_db):
        """find_by_status() should return only matching status"""
        dao = ContentDAO(temp_db)

        c1 = Content(id="t1", account_type=AccountType.A, status=ContentStatus.DRAFT)
        c2 = Content(id="t2", account_type=AccountType.A, status=ContentStatus.PENDING_REVIEW)

        dao.create(c1)
        dao.create(c2)

        drafts = dao.find_by_status(ContentStatus.DRAFT)
        assert len(drafts) == 1
        assert drafts[0].status == ContentStatus.DRAFT

    def test_update_modifies_content(self, temp_db):
        """update() should modify existing content"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.C, title="Original")
        content_id = dao.create(c)

        retrieved = dao.find_by_id(content_id)
        retrieved.title = "Modified"
        dao.update(retrieved)

        updated = dao.find_by_id(content_id)
        assert updated.title == "Modified"

    def test_find_by_id_returns_none_for_missing(self, temp_db):
        """find_by_id() should return None when id doesn't exist"""
        dao = ContentDAO(temp_db)
        result = dao.find_by_id("99999")
        assert result is None

    def test_find_by_source_url_returns_content(self, temp_db):
        """find_by_source_url() should return content by source_url"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.A, source_url="https://example.com/article1")
        content_id = dao.create(c)

        retrieved = dao.find_by_source_url("https://example.com/article1")
        assert retrieved is not None
        assert retrieved.id == content_id

    def test_find_by_source_url_skips_rejected(self, temp_db):
        """find_by_source_url() should skip REJECTED content"""
        dao = ContentDAO(temp_db)

        # Create and reject first version
        c1 = Content(id="t1", account_type=AccountType.A, source_url="https://example.com/article2", status=ContentStatus.REJECTED)
        dao.create(c1)

        # Create new version of same URL
        c2 = Content(id="t2", account_type=AccountType.A, source_url="https://example.com/article2", status=ContentStatus.DRAFT)
        content_id_2 = dao.create(c2)

        # Should return the non-rejected one
        retrieved = dao.find_by_source_url("https://example.com/article2")
        assert retrieved is not None
        assert retrieved.id == content_id_2

    def test_find_by_source_url_returns_most_recent(self, temp_db):
        """find_by_source_url() should return most recent non-rejected"""
        dao = ContentDAO(temp_db)

        # Create two non-rejected versions
        c1 = Content(id="t1", account_type=AccountType.A, source_url="https://example.com/article3", status=ContentStatus.DRAFT)
        dao.create(c1)

        c2 = Content(id="t2", account_type=AccountType.A, source_url="https://example.com/article3", status=ContentStatus.APPROVED)
        content_id_2 = dao.create(c2)

        # Should return the most recent
        retrieved = dao.find_by_source_url("https://example.com/article3")
        assert retrieved is not None
        assert retrieved.id == content_id_2

    def test_find_by_source_url_returns_none_for_missing(self, temp_db):
        """find_by_source_url() should return None for non-existent URL"""
        dao = ContentDAO(temp_db)
        result = dao.find_by_source_url("https://example.com/nonexistent")
        assert result is None

    def test_delete_removes_content(self, temp_db):
        """delete() should remove the content from the DB"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.A, title="ToDelete")
        content_id = dao.create(c)

        dao.delete(content_id)
        result = dao.find_by_id(content_id)
        assert result is None

    def test_find_by_status_with_account_type_filter(self, temp_db):
        """find_by_status() with account_type should filter by both"""
        dao = ContentDAO(temp_db)

        c1 = Content(id="t1", account_type=AccountType.A, status=ContentStatus.DRAFT)
        c2 = Content(id="t2", account_type=AccountType.B, status=ContentStatus.DRAFT)

        dao.create(c1)
        dao.create(c2)

        results = dao.find_by_status(ContentStatus.DRAFT, account_type="A")
        assert len(results) == 1
        assert results[0].account_type == AccountType.A

    def test_create_returns_string_id(self, temp_db):
        """create() should return a string ID"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.A, title="Test")
        content_id = dao.create(c)
        assert isinstance(content_id, str)

    def test_find_by_status_returns_list(self, temp_db):
        """find_by_status() should return a list even when empty"""
        dao = ContentDAO(temp_db)
        results = dao.find_by_status(ContentStatus.APPROVED)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_update_persists_status_change(self, temp_db):
        """update() should persist status changes"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.A, status=ContentStatus.DRAFT)
        content_id = dao.create(c)

        retrieved = dao.find_by_id(content_id)
        retrieved.transition_to(ContentStatus.PENDING_REVIEW)
        dao.update(retrieved)

        updated = dao.find_by_id(content_id)
        assert updated.status == ContentStatus.PENDING_REVIEW

    def test_create_multiple_contents(self, temp_db):
        """Multiple create() calls should produce unique IDs"""
        dao = ContentDAO(temp_db)
        c1 = Content(id="t1", account_type=AccountType.A, title="First")
        c2 = Content(id="t2", account_type=AccountType.B, title="Second")

        id1 = dao.create(c1)
        id2 = dao.create(c2)
        assert id1 != id2

    def test_retrieved_content_has_correct_content_type(self, temp_db):
        """Retrieved content should have the correct content_type"""
        dao = ContentDAO(temp_db)
        c = Content(
            id="temp",
            account_type=AccountType.A,
            content_type=ContentType.EDUCATIONAL
        )
        content_id = dao.create(c)

        retrieved = dao.find_by_id(content_id)
        assert retrieved.content_type == ContentType.EDUCATIONAL

    def test_platform_status_json_roundtrip(self, temp_db):
        """platform_status dict should survive DB roundtrip"""
        dao = ContentDAO(temp_db)
        c = Content(
            id="temp",
            account_type=AccountType.A,
            platform_status={"threads": "posted", "x": "pending"}
        )
        content_id = dao.create(c)

        retrieved = dao.find_by_id(content_id)
        assert retrieved.platform_status == {"threads": "posted", "x": "pending"}

    def test_malformed_json_field_falls_back_to_empty_dict(self, temp_db):
        """Malformed JSON in platform_status column should deserialize to {}"""
        import sqlite3 as _sqlite3
        # Manually insert a row with invalid JSON in platform_status
        conn = _sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO generations (account_type, status, content_type, "
            "platform_status, engagement_data, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("A", "DRAFT", "NEWS_RECAP", "not-json", "{}", "2026-01-01T00:00:00", "2026-01-01T00:00:00")
        )
        conn.commit()
        row_id = str(cursor.lastrowid)
        conn.close()

        dao = ContentDAO(temp_db)
        retrieved = dao.find_by_id(row_id)
        assert retrieved.platform_status == {}
