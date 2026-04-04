-- Migration: Add updated_at column for tracking content modifications
-- Purpose: Content dataclass expects 'updated_at' field for audit trail and state transitions
--
-- The 'updated_at' column tracks when content was last modified (status change, edit, etc.)
-- Required by Content.transition_to() which updates this field on every status change
--
-- DEFAULT value (CURRENT_TIMESTAMP) for existing rows, automatically set on INSERT

ALTER TABLE generations ADD COLUMN updated_at TEXT DEFAULT (datetime('now', 'localtime'));
