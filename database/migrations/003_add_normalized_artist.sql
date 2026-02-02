-- Migration: Add normalized_artist column to tracks table
-- This enables fast SQL-based artist filtering instead of loading all tracks into Python

-- Add normalized_artist column
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS normalized_artist VARCHAR(255);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_tracks_normalized_artist ON tracks(normalized_artist);

-- Note: Run the Python migration script to populate this field:
-- python scripts/migrate_normalized_artist.py
