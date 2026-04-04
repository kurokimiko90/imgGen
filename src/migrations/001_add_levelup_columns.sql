-- Migration: Add LevelUp Content Management Columns
-- Purpose: Extend existing 'generations' table to support multi-account content state machine
-- Version: 1.0
-- Date: 2026-03-31
--
-- These columns enable:
-- - Multi-account content classification (A / B / C)
-- - Content status machine (DRAFT → PENDING_REVIEW → APPROVED → PUBLISHED → ANALYZED)
-- - AI reasoning tracking (why was this content selected)
-- - Cross-platform publishing state
-- - Engagement metrics per content piece

-- All columns include DEFAULT values to ensure backward compatibility
-- No existing data will be modified

ALTER TABLE generations ADD COLUMN account_type TEXT DEFAULT 'A';
-- Values: 'A' (AI automation), 'B' (PMP career), 'C' (Football English)

ALTER TABLE generations ADD COLUMN status TEXT DEFAULT 'DRAFT';
-- Values: DRAFT, PENDING_REVIEW, APPROVED, PUBLISHED, ANALYZED, REJECTED
-- State machine transitions enforced at application layer

ALTER TABLE generations ADD COLUMN content_type TEXT DEFAULT 'NEWS_RECAP';
-- Values: NEWS_RECAP, PREDICTION, EDUCATIONAL
-- Categorizes the type of content for analytics and filtering

ALTER TABLE generations ADD COLUMN reasoning TEXT DEFAULT '';
-- AI-generated explanation for why this content was selected
-- Used for HITL (human-in-the-loop) review and learning

ALTER TABLE generations ADD COLUMN scheduled_time TEXT;
-- ISO 8601 datetime string (nullable)
-- When content should be published (set by audit.py during approval)

ALTER TABLE generations ADD COLUMN published_at TEXT;
-- ISO 8601 datetime string (nullable)
-- Actual publication timestamp (set by dispatcher.py after successful publishing)

ALTER TABLE generations ADD COLUMN platform_status TEXT DEFAULT '{}';
-- JSON string format: {"threads": "ok", "x": "pending", "instagram": "failed"}
-- Per-platform publishing status, updated by dispatcher.py

ALTER TABLE generations ADD COLUMN engagement_data TEXT DEFAULT '{}';
-- JSON string format: {"likes": 42, "replies": 3, "reposts": 5, "collected": 1}
-- Social engagement metrics, updated by analytics collection scripts

ALTER TABLE generations ADD COLUMN source_url TEXT;
-- Original article or content source URL (nullable)
-- Links back to the news/content that inspired this card
