-- Migration 008: ChannelMessage write-ahead pattern
-- Makes ChannelMessage the single source of truth for channel sync state.
-- Adds status field with write-ahead states: pending → sent / failed / deleted.
-- Existing records are all confirmed-sent, so they default to 'sent'.

-- 1. Add status column (all existing records are confirmed sent)
ALTER TABLE channel_messages
    ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'sent';

-- 2. Allow message_id to be NULL (PENDING records don't have one yet)
ALTER TABLE channel_messages
    ALTER COLUMN message_id DROP NOT NULL;

-- 3. Add retry tracking
ALTER TABLE channel_messages
    ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE channel_messages
    ADD COLUMN IF NOT EXISTS last_error VARCHAR(500);

-- 4. Add updated_at if not exists
ALTER TABLE channel_messages
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Backfill updated_at from created_at for existing rows
UPDATE channel_messages SET updated_at = created_at WHERE updated_at IS NULL;

-- 5. Index for efficient status queries (e.g. "find all SENT in channel")
CREATE INDEX IF NOT EXISTS idx_channel_message_status
    ON channel_messages(channel_id, status);
