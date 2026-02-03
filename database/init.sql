-- TG Player Database Schema

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_premium BOOLEAN DEFAULT FALSE,
    hide_from_search BOOLEAN DEFAULT FALSE,
    hide_profile BOOLEAN DEFAULT FALSE,
    notify_subscription BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Треки
CREATE TABLE IF NOT EXISTS tracks (
    id SERIAL PRIMARY KEY,
    uploader_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    file_id VARCHAR(255) NOT NULL,
    file_unique_id VARCHAR(255) NOT NULL,
    
    -- Метаданные
    title VARCHAR(255),
    artist VARCHAR(255),
    normalized_artist VARCHAR(255),
    album VARCHAR(255),
    genre VARCHAR(100),
    duration INTEGER,
    cover_url VARCHAR(500),
    deezer_album_id INTEGER,
    enrichment_status VARCHAR(20) DEFAULT 'pending',
    
    -- Forward source info
    forward_source_id BIGINT,
    forward_source_username VARCHAR(255),
    forward_source_name VARCHAR(255),
    forward_source_type VARCHAR(20),
    
    -- Telegram данные
    file_size INTEGER,
    mime_type VARCHAR(50),
    file_name VARCHAR(255),
    
    -- Visibility & Stats
    is_public BOOLEAN DEFAULT TRUE,
    is_unavailable BOOLEAN DEFAULT FALSE,
    play_count INTEGER DEFAULT 0,
    last_played_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Уникальность: один файл на пользователя
    UNIQUE(uploader_id, file_unique_id)
);

-- Плейлисты
CREATE TABLE IF NOT EXISTS playlists (
    id SERIAL PRIMARY KEY,
    owner_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cover_file_id VARCHAR(255),
    cover_url VARCHAR(500),
    is_public BOOLEAN DEFAULT FALSE,
    is_auto_album BOOLEAN DEFAULT FALSE,
    deezer_album_id INTEGER,
    
    -- Auto-source playlist (авто-создание по источнику пересылки)
    is_auto_source BOOLEAN DEFAULT FALSE,
    source_id BIGINT,           -- ID источника (бот/пользователь/канал)
    source_type VARCHAR(20),    -- user, bot, channel, supergroup
    
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

-- Подписки на публичные плейлисты
CREATE TABLE IF NOT EXISTS playlist_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_playlist_subscription UNIQUE (user_id, playlist_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_tracks_uploader_id ON tracks(uploader_id);
CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist);
CREATE INDEX IF NOT EXISTS idx_tracks_title ON tracks(title);
CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre);
CREATE INDEX IF NOT EXISTS idx_tracks_deezer_album_id ON tracks(deezer_album_id);
CREATE INDEX IF NOT EXISTS idx_tracks_forward_from_id ON tracks(forward_from_id) WHERE forward_from_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_playlists_owner_id ON playlists(owner_id);
CREATE INDEX IF NOT EXISTS idx_playlists_auto_source ON playlists(owner_id, is_auto_source, source_id) WHERE is_auto_source = TRUE;
CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist_id ON playlist_tracks(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_subscription_user ON playlist_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_playlist_subscription_playlist ON playlist_subscriptions(playlist_id);

-- Полнотекстовый поиск (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_tracks_search ON tracks 
    USING gin(to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(artist, '') || ' ' || coalesce(album, '')));
