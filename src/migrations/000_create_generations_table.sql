-- Migration: Create base generations table
-- Purpose: Initial schema for imgGen history tracking
-- Version: 1.0
-- Date: 2026-04-04
--
-- This is the base table that stores all generated content cards
-- Subsequent migrations add LevelUp columns for multi-account management

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
    mode             TEXT    NOT NULL DEFAULT 'single',
    extracted_data   TEXT
);

CREATE INDEX IF NOT EXISTS idx_gen_created_at ON generations(created_at);
CREATE INDEX IF NOT EXISTS idx_gen_title ON generations(title);
