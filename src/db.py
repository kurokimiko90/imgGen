"""
src/db.py - Data Access Object for Content records in the LevelUp system.

Persists Content objects into the `generations` SQLite table using
parameterized queries to prevent SQL injection.

JSON dict fields (platform_status, engagement_data) are stored as JSON
strings in the DB and deserialized back to dicts on read.
"""

import sqlite3
import json
import os
from pathlib import Path
from src.content import Content, ContentStatus


# Fields that are stored as JSON strings in the DB
_JSON_FIELDS = {'platform_status', 'engagement_data'}


class ContentDAO:
    """Data Access Object for Content records."""

    def __init__(self, db_path: str = "~/.imggen/history.db"):
        # Expand ~ to home directory and create parent dirs if needed
        self.db_path = os.path.expanduser(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Apply pending migrations idempotently."""
        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            return

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Create migrations tracking table first (idempotent)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS _migrations (
                    name TEXT PRIMARY KEY,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Get all migration files sorted by name
            migration_files = sorted(migrations_dir.glob("*.sql"))
            for migration_file in migration_files:
                migration_name = migration_file.name

                # Check if this migration has been applied
                cursor.execute(
                    "SELECT 1 FROM _migrations WHERE name = ?",
                    (migration_name,)
                )
                if cursor.fetchone() is None:
                    # Apply the migration
                    sql = migration_file.read_text(encoding="utf-8")
                    try:
                        cursor.executescript(sql)
                        cursor.execute(
                            "INSERT INTO _migrations (name) VALUES (?)",
                            (migration_name,)
                        )
                        conn.commit()
                    except sqlite3.OperationalError as e:
                        # Allow "already exists" errors (idempotent)
                        if "already exists" not in str(e).lower():
                            raise

        finally:
            conn.close()

    def _serialize_row(self, data: dict) -> dict:
        """Convert dict fields to JSON strings for DB storage."""
        result = {}
        for key, value in data.items():
            if key in _JSON_FIELDS and isinstance(value, dict):
                result[key] = json.dumps(value)
            else:
                result[key] = value
        return result

    def _deserialize_row(self, row: dict) -> dict:
        """Convert JSON string fields back to dicts after DB read."""
        result = {}
        for key, value in row.items():
            if key in _JSON_FIELDS and isinstance(value, str):
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = {}
            else:
                result[key] = value
        return result

    def create(self, content: Content) -> str:
        """Insert new content into the DB and return the assigned id.

        The content's id field is ignored — the DB assigns a new integer id.

        Args:
            content: The Content object to persist.

        Returns:
            The string representation of the new row's id.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            data = content.to_dict()
            del data['id']
            data = self._serialize_row(data)

            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            cursor.execute(
                f"INSERT INTO generations ({columns}) VALUES ({placeholders})",
                tuple(data.values())
            )
            content_id = cursor.lastrowid
            conn.commit()
            return str(content_id)
        finally:
            conn.close()

    def find_by_id(self, content_id: str) -> Content | None:
        """Retrieve a Content record by id.

        Args:
            content_id: The id to look up (string or int accepted).

        Returns:
            The matching Content object, or None if not found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM generations WHERE id = ?",
                (content_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            row_dict = self._deserialize_row(dict(row))
            row_dict['id'] = str(row_dict['id'])
            return Content.from_dict(row_dict)
        finally:
            conn.close()

    def find_by_status(
        self,
        status: ContentStatus | list[ContentStatus],
        account_type: str | None = None
    ) -> list[Content]:
        """Find all Content records with the given status(es).

        Args:
            status: A ContentStatus or list of ContentStatus objects to filter by.
            account_type: Optional account type to narrow results.

        Returns:
            List of matching Content objects ordered by created_at DESC.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Handle both single status and list of statuses
            if isinstance(status, ContentStatus):
                statuses = [status.value]
            else:
                statuses = [s.value for s in status]

            # Build placeholders for SQL IN clause
            placeholders = ', '.join(['?' for _ in statuses])

            if account_type:
                cursor.execute(
                    f"SELECT * FROM generations "
                    f"WHERE status IN ({placeholders}) AND account_type = ? "
                    f"ORDER BY created_at DESC",
                    statuses + [account_type]
                )
            else:
                cursor.execute(
                    f"SELECT * FROM generations "
                    f"WHERE status IN ({placeholders}) "
                    f"ORDER BY created_at DESC",
                    statuses
                )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                row_dict = self._deserialize_row(dict(row))
                row_dict['id'] = str(row_dict['id'])
                results.append(Content.from_dict(row_dict))
            return results
        finally:
            conn.close()

    def update(self, content: Content) -> None:
        """Update an existing Content record in the DB.

        Args:
            content: The Content object with updated fields. Its id is used
                     to identify which row to update.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            data = content.to_dict()
            content_id = data.pop('id')
            data = self._serialize_row(data)

            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            values = list(data.values()) + [content_id]

            cursor.execute(
                f"UPDATE generations SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, content_id: str) -> None:
        """Delete a Content record by id.

        Args:
            content_id: The id of the record to delete.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM generations WHERE id = ?",
                (content_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def find_by_source_url(self, source_url: str) -> Content | None:
        """Find the most recent non-rejected Content record by source URL.

        Args:
            source_url: The source URL to look up.

        Returns:
            The most recent non-rejected Content object with that URL, or None.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM generations "
                "WHERE source_url = ? AND status != ? "
                "ORDER BY created_at DESC LIMIT 1",
                (source_url, ContentStatus.REJECTED.value)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            row_dict = self._deserialize_row(dict(row))
            row_dict['id'] = str(row_dict['id'])
            return Content.from_dict(row_dict)
        finally:
            conn.close()

    def find_scheduled(
        self,
        start_date: str,
        end_date: str,
        account_type: str | None = None
    ) -> list[Content]:
        """Find APPROVED content scheduled between start_date and end_date (ISO 8601).

        Args:
            start_date: ISO date string (e.g., '2026-03-30')
            end_date: ISO date string (e.g., '2026-04-06')
            account_type: Optional account type filter.

        Returns:
            List of matching Content objects ordered by scheduled_time.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Use DATE() function for date comparison, allowing ISO datetime strings
            if account_type:
                cursor.execute(
                    "SELECT * FROM generations "
                    "WHERE status = ? "
                    "  AND DATE(scheduled_time) >= ? AND DATE(scheduled_time) <= ? "
                    "  AND account_type = ? "
                    "ORDER BY scheduled_time",
                    (ContentStatus.APPROVED.value, start_date, end_date, account_type)
                )
            else:
                cursor.execute(
                    "SELECT * FROM generations "
                    "WHERE status = ? "
                    "  AND DATE(scheduled_time) >= ? AND DATE(scheduled_time) <= ? "
                    "ORDER BY scheduled_time",
                    (ContentStatus.APPROVED.value, start_date, end_date)
                )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                row_dict = self._deserialize_row(dict(row))
                row_dict['id'] = str(row_dict['id'])
                results.append(Content.from_dict(row_dict))
            return results
        finally:
            conn.close()

    def find_drafts(
        self,
        account_type: str | None = None,
        source: str | None = None,
        days: int | None = None
    ) -> list[Content]:
        """Find DRAFT content with optional filters.

        Args:
            account_type: Optional account type filter.
            source: Optional source field filter.
            days: If specified, only include content created in last N days.

        Returns:
            List of matching DRAFT Content objects ordered by created_at DESC.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM generations WHERE status = ?"
            params = [ContentStatus.DRAFT.value]

            if account_type:
                query += " AND account_type = ?"
                params.append(account_type)

            if source:
                query += " AND source = ?"
                params.append(source)

            if days:
                query += f" AND created_at >= datetime('now', '-{days} days')"

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for row in rows:
                row_dict = self._deserialize_row(dict(row))
                row_dict['id'] = str(row_dict['id'])
                results.append(Content.from_dict(row_dict))
            return results
        finally:
            conn.close()

    def get_curation_stats(self) -> dict:
        """Get curation statistics: today/week/approval_rate per account.

        Returns:
            Dict with stats grouped by account_type.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Today's counts by account
            cursor.execute(
                "SELECT account_type, status, COUNT(*) as cnt "
                "FROM generations "
                "WHERE DATE(created_at) = DATE('now') "
                "GROUP BY account_type, status"
            )
            today_rows = cursor.fetchall()

            # This week's counts by account
            cursor.execute(
                "SELECT account_type, status, COUNT(*) as cnt "
                "FROM generations "
                "WHERE created_at >= datetime('now', '-7 days') "
                "GROUP BY account_type, status"
            )
            week_rows = cursor.fetchall()

            # Approval rate by account
            cursor.execute(
                "SELECT account_type, "
                "  COUNT(*) FILTER (WHERE status = 'APPROVED') as approved, "
                "  COUNT(*) FILTER (WHERE status = 'REJECTED') as rejected "
                "FROM generations "
                "WHERE status IN ('APPROVED', 'REJECTED') "
                "GROUP BY account_type"
            )
            approval_rows = cursor.fetchall()

            # Build result
            result = {}
            for row in today_rows:
                acct = row["account_type"] or "unknown"
                if acct not in result:
                    result[acct] = {"today": {}, "week": {}, "approval_rate": 0.0}
                result[acct]["today"][row["status"] or "unknown"] = row["cnt"]

            for row in week_rows:
                acct = row["account_type"] or "unknown"
                if acct not in result:
                    result[acct] = {"today": {}, "week": {}, "approval_rate": 0.0}
                result[acct]["week"][row["status"] or "unknown"] = row["cnt"]

            for row in approval_rows:
                acct = row["account_type"] or "unknown"
                if acct not in result:
                    result[acct] = {"today": {}, "week": {}, "approval_rate": 0.0}
                total = row["approved"] + row["rejected"]
                result[acct]["approval_rate"] = round(row["approved"] / total, 4) if total > 0 else 0.0

            return result
        finally:
            conn.close()
