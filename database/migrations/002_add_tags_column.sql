-- Migration: Add tags JSON column to track_enrichments
-- Date: 2026-02-02
-- Description: Add Last.fm tags support for detailed genre classification
-- Database: MySQL 5.7.8+

-- Add tags column (JSON array of strings)
ALTER TABLE track_enrichments
ADD COLUMN tags JSON DEFAULT NULL;

-- Note: For MySQL, JSON indexing requires a virtual/generated column
-- If you need to search by specific tag, create a virtual column:
-- ALTER TABLE track_enrichments
-- ADD COLUMN first_tag VARCHAR(100) AS (JSON_UNQUOTE(JSON_EXTRACT(tags, '$[0]'))) STORED,
-- ADD INDEX idx_enrichment_first_tag (first_tag);
