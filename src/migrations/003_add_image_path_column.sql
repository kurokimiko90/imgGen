-- Migration: Add image_path column for storing generated card images
-- Purpose: Content dataclass expects 'image_path' field to store path to generated PNG/WebP
--
-- The 'image_path' column stores the relative or absolute path to the image generated
-- by the imgGen pipeline during daily_curation.py
--
-- DEFAULT value (NULL) ensures backward compatibility with existing rows

ALTER TABLE generations ADD COLUMN image_path TEXT DEFAULT NULL;
