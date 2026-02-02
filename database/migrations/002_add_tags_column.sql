-- Migration: Add tags JSON column to track_enrichments
-- Date: 2026-02-02
-- Description: Add Last.fm tags support for detailed genre classification

-- Add tags column (JSON array of strings)
ALTER TABLE track_enrichments
ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT NULL;

-- Create GIN index for efficient tag searches
CREATE INDEX IF NOT EXISTS idx_enrichment_tags ON track_enrichments USING GIN (tags);

-- Comment for documentation
COMMENT ON COLUMN track_enrichments.tags IS 'Last.fm tags array, e.g. ["cloud rap", "trap", "drain gang"]';
