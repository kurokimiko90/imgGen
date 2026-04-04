"""
history.py - SQLite history log for all imgGen generations.

Stores metadata about every generated card so users can list, search,
and analyze their content output over time.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DB_DIR = Path.home() / ".imggen"
DB_PATH = DB_DIR / "history.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS generations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    url              TEXT,
    title            TEXT    NOT NULL,
    theme            TEXT    NOT NULL,
    format           TEXT    NOT NULL,
    provider         TEXT    NOT NULL,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    output_path      TEXT    NOT NULL,
    file_size        INTEGER,
    key_points_count INTEGER NOT NULL,
    source           TEXT,
    mode             TEXT    NOT NULL DEFAULT 'single'
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_gen_created_at ON generations(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_gen_title ON generations(title);",
]


def _connect() -> sqlite3.Connection:
    """Open (or create) the history database with WAL mode."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def _migrate_extracted_data(conn: sqlite3.Connection) -> None:
    """Add extracted_data column if it doesn't exist (v4.0 migration)."""
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(generations)").fetchall()
    }
    if "extracted_data" not in columns:
        conn.execute("ALTER TABLE generations ADD COLUMN extracted_data TEXT")
        conn.commit()


def init_db() -> None:
    """Create the generations table and indexes if they do not exist."""
    conn = _connect()
    try:
        conn.execute(_CREATE_TABLE)
        for idx_sql in _CREATE_INDEXES:
            conn.execute(idx_sql)
        conn.commit()
        _migrate_extracted_data(conn)
    finally:
        conn.close()


def record_generation(
    *,
    url: str | None = None,
    title: str,
    theme: str,
    format: str,
    provider: str,
    output_path: str,
    file_size: int | None = None,
    key_points_count: int,
    source: str | None = None,
    mode: str = "single",
    extracted_data: str | None = None,
) -> int:
    """Insert a generation record. Returns the new row id."""
    init_db()
    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO generations
                (url, title, theme, format, provider, output_path,
                 file_size, key_points_count, source, mode, extracted_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (url, title, theme, format, provider, output_path,
             file_size, key_points_count, source, mode, extracted_data),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


def get_generation_by_id(gen_id: int) -> dict[str, Any] | None:
    """Get a single generation by id. Returns None if not found."""
    init_db()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM generations WHERE id = ?", (gen_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_generation(
    gen_id: int,
    *,
    extracted_data: str | None = None,
    output_path: str | None = None,
    file_size: int | None = None,
    key_points_count: int | None = None,
    title: str | None = None,
) -> bool:
    """Update specified fields for a generation. Returns True if row was found."""
    init_db()
    conn = _connect()
    try:
        sets: list[str] = []
        vals: list[Any] = []
        if extracted_data is not None:
            sets.append("extracted_data = ?")
            vals.append(extracted_data)
        if output_path is not None:
            sets.append("output_path = ?")
            vals.append(output_path)
        if file_size is not None:
            sets.append("file_size = ?")
            vals.append(file_size)
        if key_points_count is not None:
            sets.append("key_points_count = ?")
            vals.append(key_points_count)
        if title is not None:
            sets.append("title = ?")
            vals.append(title)
        if not sets:
            return False
        vals.append(gen_id)
        cursor = conn.execute(
            f"UPDATE generations SET {', '.join(sets)} WHERE id = ?", vals
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def list_generations(
    days: int | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List recent generations, optionally filtered by days."""
    init_db()
    conn = _connect()
    try:
        if days is not None:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                "SELECT * FROM generations WHERE created_at >= ? "
                "ORDER BY created_at DESC LIMIT ?",
                (cutoff, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM generations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def search_generations(
    query: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search generations by title or URL (case-insensitive LIKE)."""
    init_db()
    conn = _connect()
    try:
        pattern = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM generations "
            "WHERE title LIKE ? OR url LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (pattern, pattern, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats(days: int | None = None) -> dict[str, Any]:
    """Return aggregate statistics about generations.

    Returns:
        Dict with keys: total, by_theme, by_provider, by_format,
        avg_points, date_range, recent_titles.
    """
    init_db()
    conn = _connect()
    try:
        where = ""
        params: tuple = ()
        if days is not None:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            where = "WHERE created_at >= ?"
            params = (cutoff,)

        # Total count
        total = conn.execute(
            f"SELECT COUNT(*) FROM generations {where}", params
        ).fetchone()[0]

        # Group by theme
        by_theme = [
            {"name": r["theme"], "count": r["cnt"]}
            for r in conn.execute(
                f"SELECT theme, COUNT(*) as cnt FROM generations {where} "
                "GROUP BY theme ORDER BY cnt DESC",
                params,
            ).fetchall()
        ]

        # Group by provider
        by_provider = [
            {"name": r["provider"], "count": r["cnt"]}
            for r in conn.execute(
                f"SELECT provider, COUNT(*) as cnt FROM generations {where} "
                "GROUP BY provider ORDER BY cnt DESC",
                params,
            ).fetchall()
        ]

        # Group by format
        by_format = [
            {"name": r["format"], "count": r["cnt"]}
            for r in conn.execute(
                f"SELECT format, COUNT(*) as cnt FROM generations {where} "
                "GROUP BY format ORDER BY cnt DESC",
                params,
            ).fetchall()
        ]

        # Average key points
        avg_row = conn.execute(
            f"SELECT AVG(key_points_count) FROM generations {where}", params
        ).fetchone()
        avg_points = round(avg_row[0], 1) if avg_row[0] is not None else 0

        # Date range
        range_row = conn.execute(
            f"SELECT MIN(created_at), MAX(created_at) FROM generations {where}",
            params,
        ).fetchone()
        date_range = {
            "earliest": range_row[0] or "",
            "latest": range_row[1] or "",
        }

        # Recent titles (last 10)
        recent_titles = [
            r["title"]
            for r in conn.execute(
                f"SELECT title FROM generations {where} "
                "ORDER BY created_at DESC LIMIT 10",
                params,
            ).fetchall()
        ]

        return {
            "total": total,
            "by_theme": by_theme,
            "by_provider": by_provider,
            "by_format": by_format,
            "avg_points": avg_points,
            "date_range": date_range,
            "recent_titles": recent_titles,
        }
    finally:
        conn.close()
