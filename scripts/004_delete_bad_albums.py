#!/usr/bin/env python3
"""
Cleanup script - Delete problematic albums
"""
import sqlite3
from pathlib import Path


def delete_album(cursor, album_id, album_name):
    """Delete album and cascade delete album_tracks entries"""
    
    # Get track count first
    cursor.execute("SELECT COUNT(*) FROM album_tracks WHERE album_id = ?", (album_id,))
    track_count = cursor.fetchone()[0]
    
    # Delete album_tracks entries (cascade)
    cursor.execute("DELETE FROM album_tracks WHERE album_id = ?", (album_id,))
    
    # Delete album
    cursor.execute("DELETE FROM albums WHERE id = ?", (album_id,))
    
    print(f'✅ Deleted album "{album_name}" (ID {album_id}) - removed {track_count} album_tracks entries')
    
    return True


def main():
    db_files = list(Path('.').glob('*.db'))
    if not db_files:
        print('❌ No SQLite database files found')
        return
    
    db_file = db_files[0]
    print(f'Database: {db_file}\n')
    
    print('=' * 60)
    print('CLEANUP: Removing albums with unknown-title tracks')
    print('=' * 60)
    
    # Albums to delete
    albums_to_delete = [
        (1355, 'МЕЖДУ ДОБРОМ И ЗЛОМ'),
        (1319, 'Металлическая изоляция'),
    ]
    
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        print('\n🔍 Verifying albums before deletion...\n')
        
        for album_id, album_name in albums_to_delete:
            cursor.execute("SELECT id, name FROM albums WHERE id = ?", (album_id,))
            result = cursor.fetchone()
            if result:
                print(f'  ✓ Found: {album_name} (ID {album_id})')
            else:
                print(f'  ✗ NOT FOUND: {album_name} (ID {album_id})')
        
        # Auto-delete
        print('\n' + '=' * 60)
        print('Proceeding with deletion (auto-confirmed)...\n')
        
        # Perform deletion
        print('🗑️  Deleting albums...\n')
        deleted_count = 0
        
        for album_id, album_name in albums_to_delete:
            if delete_album(cursor, album_id, album_name):
                deleted_count += 1
        
        # Commit changes
        conn.commit()
        
        print(f'\n✅ Successfully deleted {deleted_count} albums')
        
        # Verify deletion
        print('\n🔍 Verifying deletion...\n')
        
        for album_id, album_name in albums_to_delete:
            cursor.execute("SELECT id FROM albums WHERE id = ?", (album_id,))
            if cursor.fetchone():
                print(f'  ✗ STILL EXISTS: {album_name}')
            else:
                print(f'  ✓ DELETED: {album_name}')
        
        print('\n✅ Cleanup complete!')
        
    except Exception as e:
        conn.rollback()
        print(f'\n❌ Error during deletion: {e}')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
