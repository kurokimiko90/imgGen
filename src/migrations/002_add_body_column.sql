-- Migration: Add body column for LevelUp content management
-- Purpose: Content class expects 'body' field to store article/curation text
-- This field was missing from the previous migration
--
-- The 'body' column stores the actual content text that will be:
-- - Used in image generation
-- - Edited in ReviewPage during human review
-- - Included in the caption generation prompt
--
-- DEFAULT value ensures backward compatibility with existing rows

ALTER TABLE generations ADD COLUMN body TEXT DEFAULT '';
-- Empty string default for existing rows, real content populated by daily_curation.py
