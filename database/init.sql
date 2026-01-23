-- TG Player Database Schema

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Треки
CREATE TABLE IF NOT EXISTS tracks (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    file_id VARCHAR(255) NOT NULL,
    file_unique_id VARCHAR(255) NOT NULL,
    
    -- Метаданные
    title VARCHAR(255),
    artist VARCHAR(255),
    album VARCHAR(255),
    genre VARCHAR(100),
    duration INTEGER,
    cover_url VARCHAR(500),
    deezer_album_id INTEGER,
    enrichment_status VARCHAR(20) DEFAULT 'pending',
    
    -- Telegram данные
    file_size INTEGER,
    mime_type VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Уникальность: один файл на пользователя
    UNIQUE(user_id, file_unique_id)
);

-- Плейлисты
CREATE TABLE IF NOT EXISTS playlists (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cover_file_id VARCHAR(255),
    cover_url VARCHAR(500),
    is_public BOOLEAN DEFAULT FALSE,
    is_auto_album BOOLEAN DEFAULT FALSE,
    deezer_album_id INTEGER,
    share_code VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Связь плейлистов и треков
CREATE TABLE IF NOT EXISTS playlist_tracks (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER REFERENCES playlists(id) ON DELETE CASCADE,
    track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(playlist_id, track_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_tracks_user_id ON tracks(user_id);
CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist);
CREATE INDEX IF NOT EXISTS idx_tracks_title ON tracks(title);
CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre);
CREATE INDEX IF NOT EXISTS idx_tracks_deezer_album_id ON tracks(deezer_album_id);
CREATE INDEX IF NOT EXISTS idx_playlists_user_id ON playlists(user_id);
CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist_id ON playlist_tracks(playlist_id);

-- Полнотекстовый поиск (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_tracks_search ON tracks 
    USING gin(to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(artist, '') || ' ' || coalesce(album, '')));
