-- Add review_scores JSON column to generations table
ALTER TABLE generations ADD COLUMN review_scores TEXT DEFAULT '{}';

-- Learnings table: stores patterns extracted from review history (no LLM needed)
CREATE TABLE IF NOT EXISTS learnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_type TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('design', 'copy', 'tone', 'failure')),
    rule TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5,
    sample_count INTEGER NOT NULL DEFAULT 1,
    avg_score REAL,
    first_seen TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen TEXT NOT NULL DEFAULT (datetime('now')),
    active BOOLEAN NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_learnings_account ON learnings(account_type, category, active);
