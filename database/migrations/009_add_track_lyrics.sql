-- Migration 009: Add track lyrics table
CREATE TABLE IF NOT EXISTS track_lyrics (
    id SERIAL PRIMARY KEY,
    track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    plain_lyrics TEXT,
    synced_lyrics TEXT,
    is_synced BOOLEAN DEFAULT FALSE,
    is_instrumental BOOLEAN DEFAULT FALSE,
    source VARCHAR(50) DEFAULT 'lrclib',
    offset_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_track_lyrics_track UNIQUE (track_id)
);

CREATE INDEX IF NOT EXISTS idx_track_lyrics_track ON track_lyrics(track_id);
