#!/usr/bin/env python3
"""
Diagnostic script - Check for problem albums

This script diagnoses and reports on problematic albums without requiring active DB connections.
"""
import os
import sqlite3
from pathlib import Path

def check_sqlite_db():
    """Check local SQLite database if it exists"""
    db_files = list(Path('.').glob('*.db'))
    
    if not db_files:
        print('❌ No SQLite database files found (.db files)')
        print('   Check if database is PostgreSQL in Docker instead')
        return False
    
    db_file = db_files[0]
    print(f'✅ Found SQLite database: {db_file}')
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='albums'")
        if not cursor.fetchone():
            print('❌ No albums table found in database')
            conn.close()
            return False
        
        # Look for the problematic album
        cursor.execute(
            "SELECT id, name, artist FROM albums WHERE LOWER(name) = 'между добром и злом'"
        )
        album = cursor.fetchone()
        
        if album:
            album_id, name, artist = album
            print(f'\n✅ Album FOUND:')
            print(f'   ID: {album_id}')
            print(f'   Name: {name}')
            print(f'   Artist: {artist}')
            
            # Get tracks in album
            cursor.execute(
                """SELECT t.id, t.title, t.artist FROM album_tracks at
                   JOIN tracks t ON at.track_id = t.id
                   WHERE at.album_id = ?""",
                (album_id,)
            )
            tracks = cursor.fetchall()
            print(f'\n   Tracks in album: {len(tracks)}')
            
            for track_id, title, track_artist in tracks:
                print(f'   - Track {track_id}: "{title or "Без названия"}" by "{track_artist or "Unknown"}"')
            
            # Check for unknown titles
            unknown = any(not title for _, title, _ in tracks)
            if unknown:
                print('\n   ⚠️  FOUND TRACKS WITHOUT TITLE - This is the issue!')
            
            conn.close()
            return album_id
        else:
            print('❌ Album "МЕЖДУ ДОБРОМ И ЗЛОМ" not found')
            
            # List all albums
            cursor.execute("SELECT COUNT(*) FROM albums")
            count = cursor.fetchone()[0]
            print(f'\n📋 Total albums in database: {count}')
            
            cursor.execute("SELECT id, name, artist FROM albums LIMIT 10")
            albums = cursor.fetchall()
            
            if albums:
                print('\n   First albums:')
                for aid, aname, aartist in albums:
                    cursor.execute(
                        "SELECT COUNT(*) FROM album_tracks WHERE album_id = ?",
                        (aid,)
                    )
                    track_count = cursor.fetchone()[0]
                    print(f'   - "{aname}" by "{aartist}" ({track_count} tracks)')
            
            conn.close()
            return None
    
    except Exception as e:
        print(f'❌ Error accessing database: {e}')
        return False


def main():
    print('=== TG Player Album Diagnostic ===\n')
    
    db_url = os.getenv('DATABASE_URL', '').lower()
    
    if 'postgresql' in db_url:
        print('📌 Database configured as PostgreSQL')
        print('   Make sure Docker is running: docker-compose up -d')
        print('   Or switch to SQLite in .env.local\n')
        
        # Try to show SQLite fallback
        if Path('.').glob('*.db'):
            print('   Found local SQLite files - using those instead...\n')
            check_sqlite_db()
        else:
            print('   No local SQLite files found')
    elif 'sqlite' in db_url or not db_url:
        print('📌 Database configured as SQLite\n')
        check_sqlite_db()
    else:
        print(f'⚠️  Unknown database type: {db_url}')


if __name__ == '__main__':
    main()

