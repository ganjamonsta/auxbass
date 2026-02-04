-- Fix users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS hide_from_search BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS hide_profile BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_subscription BOOLEAN DEFAULT TRUE;

-- Fix tracks table - Add missing columns
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS normalized_artist VARCHAR(255);
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE;
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS is_unavailable BOOLEAN DEFAULT FALSE;
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS play_count INTEGER DEFAULT 0;
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS last_played_at TIMESTAMP;

-- Rename columns to match V2 models
-- Postgres 9.0+ supports IF EXISTS for generic ALTER but renaming columns is specific
DO $$
BEGIN
  -- Link to User model (uploader_id)
  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='tracks' AND column_name='user_id') THEN
    ALTER TABLE tracks RENAME COLUMN user_id TO uploader_id;
  END IF;
  
  -- Forward Source fields
  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='tracks' AND column_name='forward_from_id') THEN
    ALTER TABLE tracks RENAME COLUMN forward_from_id TO forward_source_id;
  END IF;

  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='tracks' AND column_name='forward_from_username') THEN
    ALTER TABLE tracks RENAME COLUMN forward_from_username TO forward_source_username;
  END IF;

  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='tracks' AND column_name='forward_from_name') THEN
    ALTER TABLE tracks RENAME COLUMN forward_from_name TO forward_source_name;
  END IF;

  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='tracks' AND column_name='forward_from_type') THEN
    ALTER TABLE tracks RENAME COLUMN forward_from_type TO forward_source_type;
  END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tracks_normalized_artist ON tracks(normalized_artist);
