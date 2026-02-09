-- Migration 007: User-generated track tags with voting system
-- Tags can come from enrichment (Last.fm) or be manually added by users.
-- Users can vote/endorse tags to confirm relevance.

-- Track tags table: one row per unique tag per track
CREATE TABLE IF NOT EXISTS track_tags (
    id SERIAL PRIMARY KEY,
    track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,               -- Normalized: lowercase, trimmed
    source VARCHAR(20) NOT NULL DEFAULT 'user',  -- 'enrichment' or 'user'
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_track_tag UNIQUE (track_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_track_tag_track ON track_tags(track_id);
CREATE INDEX IF NOT EXISTS idx_track_tag_name ON track_tags(tag);

-- Track tag votes: one vote per user per tag
CREATE TABLE IF NOT EXISTS track_tag_votes (
    id SERIAL PRIMARY KEY,
    track_tag_id INTEGER NOT NULL REFERENCES track_tags(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_track_tag_vote UNIQUE (track_tag_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_track_tag_vote_user ON track_tag_votes(user_id);

-- Migrate existing enrichment tags into the new track_tags table.
-- This populates the normalized table from the JSON column in track_enrichments.
-- Uses jsonb_array_elements_text to unpack the JSON array.
INSERT INTO track_tags (track_id, tag, source, created_at)
SELECT 
    te.track_id,
    lower(trim(t.value)) AS tag,
    'enrichment' AS source,
    te.enriched_at
FROM track_enrichments te,
     jsonb_array_elements_text(te.tags::jsonb) AS t(value)
WHERE te.tags IS NOT NULL
ON CONFLICT (track_id, tag) DO NOTHING;
