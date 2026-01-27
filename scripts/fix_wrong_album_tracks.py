#!/usr/bin/env python3
"""
Fix wrongly assigned album tracks.

Checks each track in album_tracks against its enrichment data
and removes tracks that don't belong to the album.
"""
import sqlite3

conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

# Get table names
c.execute('SELECT name FROM sqlite_master WHERE type="table"')
print("Tables:", [r[0] for r in c.fetchall()])

# Find enrichment table name
c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%enrich%"')
enrich_tables = [r[0] for r in c.fetchall()]
print("Enrichment tables:", enrich_tables)

if enrich_tables:
    enrich_table = enrich_tables[0]
    
    # Get tracks in album 13 (333) with their enrichment album_name
    c.execute(f'''
        SELECT at.id, t.id, t.title, t.artist, e.album_name, a.name as current_album
        FROM album_tracks at
        JOIN tracks t ON t.id = at.track_id
        JOIN albums a ON a.id = at.album_id
        LEFT JOIN {enrich_table} e ON e.track_id = t.id
        WHERE at.album_id = 13
        ORDER BY t.title
    ''')
    
    print("\nTracks in album 13 (333):")
    wrong_tracks = []
    for r in c.fetchall():
        at_id, t_id, title, artist, enrich_album, current_album = r
        match = "✓" if enrich_album and "333" in enrich_album else "✗ WRONG"
        print(f"  {title} by {artist} -> enrichment: {enrich_album} {match}")
        if enrich_album and "333" not in enrich_album:
            wrong_tracks.append((at_id, t_id, title, enrich_album))
    
    print(f"\nWrong tracks to remove: {len(wrong_tracks)}")
    for at_id, t_id, title, enrich_album in wrong_tracks:
        print(f"  Removing: {title} (belongs to: {enrich_album})")
        c.execute('DELETE FROM album_tracks WHERE id = ?', (at_id,))
    
    conn.commit()
    print("Done!")

conn.close()
