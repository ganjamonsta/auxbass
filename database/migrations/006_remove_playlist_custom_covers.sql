-- Migration: Remove custom playlist cover fields
-- These fields were used for custom cover upload functionality that has been removed

-- Remove cover_url from playlists (custom cover URL)
ALTER TABLE playlists DROP COLUMN IF EXISTS cover_url;

-- Remove pending_cover_file_id from playlists (temporary file_id before save)
ALTER TABLE playlists DROP COLUMN IF EXISTS pending_cover_file_id;

-- Remove cover_message_id from playlists (message ID in channel for deletion when updating)
ALTER TABLE playlists DROP COLUMN IF EXISTS cover_message_id;

-- Remove cover_file_id from playlists (legacy field from init.sql)
ALTER TABLE playlists DROP COLUMN IF EXISTS cover_file_id;
