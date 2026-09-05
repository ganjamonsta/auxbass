-- Migration: Add custom_cover_url to playlists and is_disliked/disliked_at to user_library

ALTER TABLE playlists ADD COLUMN IF NOT EXISTS custom_cover_url VARCHAR(500);

ALTER TABLE user_library ADD COLUMN IF NOT EXISTS is_disliked BOOLEAN DEFAULT 0;
ALTER TABLE user_library ADD COLUMN IF NOT EXISTS disliked_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_user_library_disliked ON user_library(user_id, is_disliked);
