"""
src/learning.py - Learning data access for the elite review system.

Stores and queries patterns extracted from review scores.
Uses SQLite (same DB as ContentDAO) — no YAML, no LLM needed for aggregation.
"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Pattern:
    """A learned pattern from review history."""
    id: int
    account_type: str
    category: str  # design, copy, tone, failure
    rule: str
    confidence: float
    sample_count: int
    avg_score: Optional[float]


class LearningDAO:
    """Data access for the learnings table."""

    def __init__(self, db_path: str = "~/.imggen/history.db"):
        self.db_path = str(Path(db_path).expanduser())

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def record_review(self, content_id: str, scores: dict) -> None:
        """Save review scores to the generations table.

        Args:
            content_id: The content record ID.
            scores: Dict like {"content": 7.5, "visual": 8.0, "weighted": 7.7}
        """
        conn = self._conn()
        try:
            conn.execute(
                "UPDATE generations SET review_scores = ? WHERE id = ?",
                (json.dumps(scores), content_id),
            )
            conn.commit()
        finally:
            conn.close()

    def upsert_pattern(
        self,
        account_type: str,
        category: str,
        rule: str,
        avg_score: float,
    ) -> None:
        """Insert or update a learning pattern.

        If the same (account_type, category, rule) exists, increment sample_count
        and update avg_score with running average.
        """
        conn = self._conn()
        try:
            existing = conn.execute(
                "SELECT id, sample_count, avg_score FROM learnings "
                "WHERE account_type = ? AND category = ? AND rule = ? AND active = 1",
                (account_type, category, rule),
            ).fetchone()

            if existing:
                new_count = existing["sample_count"] + 1
                # Running average
                old_avg = existing["avg_score"] or avg_score
                new_avg = old_avg + (avg_score - old_avg) / new_count
                # Confidence grows with samples, caps at 0.95
                confidence = min(0.95, 0.5 + (new_count - 1) * 0.05)

                conn.execute(
                    "UPDATE learnings SET sample_count = ?, avg_score = ?, "
                    "confidence = ?, last_seen = datetime('now') WHERE id = ?",
                    (new_count, round(new_avg, 2), round(confidence, 2), existing["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO learnings (account_type, category, rule, confidence, "
                    "sample_count, avg_score) VALUES (?, ?, ?, 0.5, 1, ?)",
                    (account_type, category, rule, avg_score),
                )
            conn.commit()
        finally:
            conn.close()

    def get_top_patterns(
        self,
        account_type: str,
        category: Optional[str] = None,
        limit: int = 5,
    ) -> list[Pattern]:
        """Get top patterns by confidence × avg_score, descending."""
        conn = self._conn()
        try:
            query = (
                "SELECT * FROM learnings "
                "WHERE account_type = ? AND active = 1 AND category != 'failure'"
            )
            params: list = [account_type]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY (confidence * COALESCE(avg_score, 0)) DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [
                Pattern(
                    id=r["id"],
                    account_type=r["account_type"],
                    category=r["category"],
                    rule=r["rule"],
                    confidence=r["confidence"],
                    sample_count=r["sample_count"],
                    avg_score=r["avg_score"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_top_failures(
        self,
        account_type: str,
        limit: int = 3,
    ) -> list[Pattern]:
        """Get top failure patterns (lowest avg_score first)."""
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM learnings "
                "WHERE account_type = ? AND active = 1 AND category = 'failure' "
                "ORDER BY avg_score ASC LIMIT ?",
                (account_type, limit),
            ).fetchall()
            return [
                Pattern(
                    id=r["id"],
                    account_type=r["account_type"],
                    category=r["category"],
                    rule=r["rule"],
                    confidence=r["confidence"],
                    sample_count=r["sample_count"],
                    avg_score=r["avg_score"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_account_stats(self, account_type: str) -> dict:
        """Get aggregate review stats for an account (pure SQL, no LLM)."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT "
                "  COUNT(*) as total, "
                "  AVG(json_extract(review_scores, '$.weighted')) as avg_score, "
                "  SUM(CASE WHEN json_extract(review_scores, '$.weighted') >= 7.5 THEN 1 ELSE 0 END) as passed "
                "FROM generations "
                "WHERE account_type = ? AND review_scores != '{}'",
                (account_type,),
            ).fetchone()

            total = row["total"] or 0
            return {
                "total_reviewed": total,
                "avg_score": round(row["avg_score"] or 0, 2),
                "pass_rate": round((row["passed"] or 0) / total, 2) if total > 0 else 0,
            }
        finally:
            conn.close()
