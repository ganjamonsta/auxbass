#!/usr/bin/env python3
"""
Migration script: v1 -> v2 database schema

This script migrates data from the old schema to the new one:
1. Creates new tables (v2 schema)
2. Migrates users (no changes needed)
3. Migrates tracks (split enrichment data into TrackEnrichment)
4. Creates Albums from auto-album playlists
5. Migrates user_library
6. Migrates user playlists (only non-auto ones)
7. Creates SourceCollections from auto-source playlists

Run with: python migrate_v2.py
"""
import asyncio
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))


def normalize_text(text: str) -> str:
    """Normalize text for matching (lowercase, remove special chars)"""
    if not text:
        return ""
    import re
    import unicodedata
    
    text = unicodedata.normalize('NFKD', text)
    text = text.lower().strip()
    text = re.sub(r'\s*[\(\[][^\)\]]*[\)\]]', '', text)  # Remove parentheses
    text = text.replace('&', '').replace('$', 's')
    text = re.sub(r'[^\w\s]', '', text)
    text = ' '.join(text.split())
    return text


def normalize_artist(artist: str) -> str:
    """Normalize artist name (take first artist, remove feat, etc.)"""
    if not artist:
        return ""
    import re
    
    artist = normalize_text(artist)
    # Remove feat., prod., etc.
    artist = re.sub(r'\s*(feat|ft|featuring|vs|prod|produced\s+by)\s+.*', '', artist)
    # Take first artist
    artist = re.split(r'\s*[,&+]\s*|\s+(?:x|and|with)\s+', artist)[0]
    return artist.strip()


class MigrationV2:
    def __init__(self, db_path: str = "tg_player.db", new_db_path: str = "tg_player_v2.db"):
        self.old_db_path = db_path
        self.new_db_path = new_db_path
        self.old_conn = None
        self.new_conn = None
        
        # Mapping old IDs to new IDs
        self.track_id_map = {}  # old_id -> new_id
        self.album_id_map = {}  # (normalized_name, normalized_artist) -> new_id
        self.playlist_id_map = {}  # old_id -> new_id
        
    def connect(self):
        """Connect to both databases"""
        self.old_conn = sqlite3.connect(self.old_db_path)
        self.old_conn.row_factory = sqlite3.Row
        
        # Create new database
        if Path(self.new_db_path).exists():
            Path(self.new_db_path).unlink()
        self.new_conn = sqlite3.connect(self.new_db_path)
        
    def close(self):
        """Close connections"""
        if self.old_conn:
            self.old_conn.close()
        if self.new_conn:
            self.new_conn.close()
            
    def create_new_schema(self):
        """Create v2 schema in new database"""
        print("Creating v2 schema...")
        
        self.new_conn.executescript("""
        -- Users (same as before)
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            is_premium BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tracks (simplified)
        CREATE TABLE tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id VARCHAR(255) NOT NULL,
            file_unique_id VARCHAR(255) NOT NULL UNIQUE,
            file_size INTEGER,
            mime_type VARCHAR(50),
            title VARCHAR(255),
            artist VARCHAR(255),
            duration INTEGER,
            uploader_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            is_public BOOLEAN NOT NULL DEFAULT 1,
            is_unavailable BOOLEAN NOT NULL DEFAULT 0,
            enrichment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            play_count INTEGER NOT NULL DEFAULT 0,
            last_played_at DATETIME,
            forward_source_type VARCHAR(20),
            forward_source_id INTEGER,
            forward_source_name VARCHAR(255),
            forward_source_username VARCHAR(255),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_tracks_artist ON tracks(artist);
        CREATE INDEX idx_tracks_title ON tracks(title);
        CREATE INDEX idx_tracks_uploader ON tracks(uploader_id);
        CREATE INDEX idx_tracks_enrichment ON tracks(enrichment_status);
        
        -- Track Enrichment (separated from tracks)
        CREATE TABLE track_enrichments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL UNIQUE REFERENCES tracks(id) ON DELETE CASCADE,
            album_name VARCHAR(255),
            genre VARCHAR(100),
            cover_url VARCHAR(500),
            release_date VARCHAR(20),
            track_number INTEGER,
            deezer_track_id INTEGER,
            deezer_album_id INTEGER,
            lastfm_url VARCHAR(500),
            musicbrainz_id VARCHAR(50),
            confidence INTEGER NOT NULL DEFAULT 0,
            enriched_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_enrichment_deezer_album ON track_enrichments(deezer_album_id);
        CREATE INDEX idx_enrichment_album_name ON track_enrichments(album_name);
        
        -- Albums (new entity)
        CREATE TABLE albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            artist VARCHAR(255) NOT NULL,
            normalized_name VARCHAR(255) NOT NULL,
            normalized_artist VARCHAR(255) NOT NULL,
            cover_url VARCHAR(500),
            release_date VARCHAR(20),
            total_tracks INTEGER,
            deezer_album_id INTEGER UNIQUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(normalized_name, normalized_artist)
        );
        CREATE INDEX idx_album_artist ON albums(normalized_artist);
        CREATE INDEX idx_album_deezer ON albums(deezer_album_id);
        
        -- Album Tracks
        CREATE TABLE album_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id INTEGER NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
            track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
            track_number INTEGER NOT NULL DEFAULT 0,
            added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(album_id, track_id)
        );
        
        -- User Library
        CREATE TABLE user_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
            source VARCHAR(20) NOT NULL DEFAULT 'uploaded',
            is_liked BOOLEAN NOT NULL DEFAULT 0,
            liked_at DATETIME,
            play_count INTEGER NOT NULL DEFAULT 0,
            last_played_at DATETIME,
            added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, track_id)
        );
        CREATE INDEX idx_user_library_user ON user_library(user_id);
        CREATE INDEX idx_user_library_liked ON user_library(user_id, is_liked);
        
        -- Playlists (user-created only)
        CREATE TABLE playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            cover_url VARCHAR(500),
            is_public BOOLEAN NOT NULL DEFAULT 0,
            share_code VARCHAR(50) UNIQUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Playlist Tracks
        CREATE TABLE playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
            track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
            position INTEGER NOT NULL,
            added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(playlist_id, track_id)
        );
        
        -- Source Collections (auto-playlists by forward source)
        CREATE TABLE source_collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_type VARCHAR(20) NOT NULL,
            source_id INTEGER,
            source_name VARCHAR(255) NOT NULL,
            source_username VARCHAR(255),
            cover_url VARCHAR(500),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(owner_id, source_type, source_id)
        );
        CREATE INDEX idx_source_collection_owner ON source_collections(owner_id);
        
        -- Source Collection Tracks
        CREATE TABLE source_collection_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_id INTEGER NOT NULL REFERENCES source_collections(id) ON DELETE CASCADE,
            track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
            added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(collection_id, track_id)
        );
        
        -- User Channels (new feature)
        CREATE TABLE user_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            channel_id INTEGER NOT NULL,
            channel_username VARCHAR(255),
            channel_title VARCHAR(255),
            is_active BOOLEAN NOT NULL DEFAULT 1,
            auto_forward BOOLEAN NOT NULL DEFAULT 1,
            include_hashtags BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Channel Messages
        CREATE TABLE channel_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL REFERENCES user_channels(id) ON DELETE CASCADE,
            track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
            message_id INTEGER NOT NULL,
            hashtags TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(channel_id, track_id)
        );
        CREATE INDEX idx_channel_message_track ON channel_messages(track_id);
        """)
        
        self.new_conn.commit()
        print("  ✓ Schema created")
        
    def migrate_users(self):
        """Migrate users table (no changes needed)"""
        print("Migrating users...")
        
        cursor = self.old_conn.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        for user in users:
            self.new_conn.execute("""
                INSERT INTO users (id, username, first_name, last_name, is_premium, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user['id'], user['username'], user['first_name'], user['last_name'],
                  user['is_premium'], user['created_at'], user['updated_at']))
        
        self.new_conn.commit()
        print(f"  ✓ Migrated {len(users)} users")
        
    def migrate_tracks(self):
        """Migrate tracks and split enrichment data"""
        print("Migrating tracks...")
        
        cursor = self.old_conn.execute("SELECT * FROM tracks")
        tracks = cursor.fetchall()
        
        enriched_count = 0
        
        for track in tracks:
            # Normalize enrichment_status
            status = track['enrichment_status']
            if status == 'success':
                status = 'completed'
            elif status not in ('pending', 'processing', 'completed', 'failed'):
                status = 'pending'
            
            # Insert track (without enrichment data)
            cursor = self.new_conn.execute("""
                INSERT INTO tracks (
                    file_id, file_unique_id, file_size, mime_type,
                    title, artist, duration, uploader_id,
                    is_public, is_unavailable, enrichment_status,
                    play_count, last_played_at,
                    forward_source_type, forward_source_id, forward_source_name, forward_source_username,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                track['file_id'], track['file_unique_id'], track['file_size'], track['mime_type'],
                track['title'], track['artist'], track['duration'], track['user_id'],
                track['is_public'] if track['is_public'] is not None else 1,
                track['is_unavailable'] if track['is_unavailable'] is not None else 0,
                status,
                track['play_count'] or 0, track['last_played_at'],
                track['forward_from_type'], track['forward_from_id'],
                track['forward_from_name'], track['forward_from_username'],
                track['created_at'], track['updated_at']
            ))
            
            new_track_id = cursor.lastrowid
            self.track_id_map[track['id']] = new_track_id
            
            # Create enrichment record if track has enrichment data
            has_enrichment = (
                track['album'] or track['genre'] or track['cover_url'] or track['deezer_album_id']
            )
            
            if has_enrichment and status in ('completed', 'success'):
                self.new_conn.execute("""
                    INSERT INTO track_enrichments (
                        track_id, album_name, genre, cover_url, deezer_album_id, confidence
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    new_track_id,
                    track['album'], track['genre'], track['cover_url'],
                    track['deezer_album_id'],
                    80 if track['deezer_album_id'] else 50  # Higher confidence if we have Deezer ID
                ))
                enriched_count += 1
        
        self.new_conn.commit()
        print(f"  ✓ Migrated {len(tracks)} tracks")
        print(f"  ✓ Created {enriched_count} enrichment records")
        
    def migrate_albums(self):
        """Create albums from auto-album playlists"""
        print("Migrating albums...")
        
        cursor = self.old_conn.execute("""
            SELECT p.*, COUNT(pt.id) as track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON pt.playlist_id = p.id
            WHERE p.is_auto_album = 1
            GROUP BY p.id
        """)
        auto_albums = cursor.fetchall()
        
        created_count = 0
        merged_count = 0
        
        for album in auto_albums:
            if album['track_count'] == 0:
                continue
                
            name = album['name']
            artist = album['album_artist'] or 'Unknown'
            normalized_name = normalize_text(name)
            normalized_artist = normalize_artist(artist)
            
            key = (normalized_name, normalized_artist)
            
            if key in self.album_id_map:
                # Album already exists (merge)
                merged_count += 1
                album_id = self.album_id_map[key]
            else:
                # Create new album
                try:
                    cursor = self.new_conn.execute("""
                        INSERT INTO albums (
                            name, artist, normalized_name, normalized_artist,
                            cover_url, release_date, deezer_album_id
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name, artist, normalized_name, normalized_artist,
                        album['cover_url'], album['release_date'], album['deezer_album_id']
                    ))
                    album_id = cursor.lastrowid
                    self.album_id_map[key] = album_id
                    created_count += 1
                except sqlite3.IntegrityError:
                    # Duplicate - get existing
                    cursor = self.new_conn.execute("""
                        SELECT id FROM albums WHERE normalized_name = ? AND normalized_artist = ?
                    """, (normalized_name, normalized_artist))
                    row = cursor.fetchone()
                    if row:
                        album_id = row[0]
                        self.album_id_map[key] = album_id
                        merged_count += 1
                    else:
                        continue
            
            # Migrate tracks for this album
            tracks_cursor = self.old_conn.execute("""
                SELECT track_id, position FROM playlist_tracks WHERE playlist_id = ?
            """, (album['id'],))
            
            for pt in tracks_cursor.fetchall():
                old_track_id = pt['track_id']
                if old_track_id in self.track_id_map:
                    new_track_id = self.track_id_map[old_track_id]
                    try:
                        self.new_conn.execute("""
                            INSERT OR IGNORE INTO album_tracks (album_id, track_id, track_number)
                            VALUES (?, ?, ?)
                        """, (album_id, new_track_id, pt['position']))
                    except sqlite3.IntegrityError:
                        pass
        
        self.new_conn.commit()
        print(f"  ✓ Created {created_count} albums")
        print(f"  ✓ Merged {merged_count} duplicate albums")
        
    def migrate_user_library(self):
        """Migrate user library entries"""
        print("Migrating user library...")
        
        cursor = self.old_conn.execute("SELECT * FROM user_library")
        entries = cursor.fetchall()
        
        migrated = 0
        for entry in entries:
            old_track_id = entry['track_id']
            if old_track_id not in self.track_id_map:
                continue
                
            new_track_id = self.track_id_map[old_track_id]
            
            try:
                self.new_conn.execute("""
                    INSERT INTO user_library (
                        user_id, track_id, source, is_liked, liked_at,
                        play_count, last_played_at, added_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry['user_id'], new_track_id,
                    entry['source'] or 'uploaded',
                    entry['is_liked'] or 0, entry['liked_at'],
                    entry['play_count'] or 0, entry['last_played_at'],
                    entry['added_at']
                ))
                migrated += 1
            except sqlite3.IntegrityError:
                pass
        
        self.new_conn.commit()
        print(f"  ✓ Migrated {migrated} library entries")
        
    def migrate_playlists(self):
        """Migrate user-created playlists (not auto-albums or auto-source)"""
        print("Migrating user playlists...")
        
        cursor = self.old_conn.execute("""
            SELECT * FROM playlists
            WHERE (is_auto_album IS NULL OR is_auto_album = 0)
              AND (is_auto_source IS NULL OR is_auto_source = 0)
        """)
        playlists = cursor.fetchall()
        
        for playlist in playlists:
            cursor = self.new_conn.execute("""
                INSERT INTO playlists (
                    owner_id, name, description, cover_url,
                    is_public, share_code, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                playlist['user_id'], playlist['name'], playlist['description'],
                playlist['cover_url'], playlist['is_public'],
                playlist['share_code'], playlist['created_at'], playlist['updated_at']
            ))
            
            new_playlist_id = cursor.lastrowid
            self.playlist_id_map[playlist['id']] = new_playlist_id
            
            # Migrate playlist tracks
            tracks_cursor = self.old_conn.execute("""
                SELECT * FROM playlist_tracks WHERE playlist_id = ?
            """, (playlist['id'],))
            
            for pt in tracks_cursor.fetchall():
                old_track_id = pt['track_id']
                if old_track_id in self.track_id_map:
                    new_track_id = self.track_id_map[old_track_id]
                    try:
                        self.new_conn.execute("""
                            INSERT INTO playlist_tracks (playlist_id, track_id, position, added_at)
                            VALUES (?, ?, ?, ?)
                        """, (new_playlist_id, new_track_id, pt['position'], pt['added_at']))
                    except sqlite3.IntegrityError:
                        pass
        
        self.new_conn.commit()
        print(f"  ✓ Migrated {len(playlists)} user playlists")
        
    def migrate_source_collections(self):
        """Migrate auto-source playlists to source collections"""
        print("Migrating source collections...")
        
        cursor = self.old_conn.execute("""
            SELECT * FROM playlists WHERE is_auto_source = 1
        """)
        source_playlists = cursor.fetchall()
        
        for sp in source_playlists:
            try:
                cursor = self.new_conn.execute("""
                    INSERT INTO source_collections (
                        owner_id, source_type, source_id, source_name, source_username,
                        cover_url, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sp['user_id'], sp['source_type'], sp['source_id'],
                    sp['name'], None,  # We don't have username in old schema
                    sp['cover_url'], sp['created_at'], sp['updated_at']
                ))
                
                collection_id = cursor.lastrowid
                
                # Migrate tracks
                tracks_cursor = self.old_conn.execute("""
                    SELECT * FROM playlist_tracks WHERE playlist_id = ?
                """, (sp['id'],))
                
                for pt in tracks_cursor.fetchall():
                    old_track_id = pt['track_id']
                    if old_track_id in self.track_id_map:
                        new_track_id = self.track_id_map[old_track_id]
                        try:
                            self.new_conn.execute("""
                                INSERT INTO source_collection_tracks (collection_id, track_id, added_at)
                                VALUES (?, ?, ?)
                            """, (collection_id, new_track_id, pt['added_at']))
                        except sqlite3.IntegrityError:
                            pass
                            
            except sqlite3.IntegrityError:
                pass
        
        self.new_conn.commit()
        print(f"  ✓ Migrated {len(source_playlists)} source collections")
        
    def verify_migration(self):
        """Verify migration results"""
        print("\n=== VERIFICATION ===")
        
        tables = [
            'users', 'tracks', 'track_enrichments', 'albums', 'album_tracks',
            'user_library', 'playlists', 'playlist_tracks',
            'source_collections', 'source_collection_tracks'
        ]
        
        for table in tables:
            cursor = self.new_conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows")
            
    def run(self):
        """Run full migration"""
        print("=" * 60)
        print("TG Player Database Migration: v1 -> v2")
        print("=" * 60)
        print()
        
        try:
            self.connect()
            self.create_new_schema()
            self.migrate_users()
            self.migrate_tracks()
            self.migrate_albums()
            self.migrate_user_library()
            self.migrate_playlists()
            self.migrate_source_collections()
            self.verify_migration()
            
            print()
            print("=" * 60)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print(f"   New database: {self.new_db_path}")
            print("=" * 60)
            
        finally:
            self.close()


if __name__ == "__main__":
    migration = MigrationV2()
    migration.run()
