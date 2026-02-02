-- Migration: Add file_name column to tracks table
-- Purpose: Store original filename for display when metadata is missing

-- Add file_name column
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);

-- Comment for documentation
COMMENT ON COLUMN tracks.file_name IS 'Original filename from Telegram, used as fallback display when title is missing';
