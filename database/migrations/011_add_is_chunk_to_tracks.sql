-- Migration 011: Add is_chunk and source_url to tracks
-- Used for 30s quick preview chunks in external music search

ALTER TABLE tracks ADD COLUMN is_chunk BOOLEAN DEFAULT FALSE;
ALTER TABLE tracks ADD COLUMN source_url VARCHAR(500);

CREATE INDEX IF NOT EXISTS idx_tracks_is_chunk ON tracks(is_chunk);
