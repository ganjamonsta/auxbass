-- Migration: Add pending_cover_file_id and cover_message_id to playlists
-- pending_cover_file_id: temporary file_id before user clicks Save
-- cover_message_id: message ID in channel for deletion when updating cover

ALTER TABLE playlists ADD COLUMN IF NOT EXISTS pending_cover_file_id VARCHAR(255);
ALTER TABLE playlists ADD COLUMN IF NOT EXISTS cover_message_id BIGINT;
