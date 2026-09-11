#!/usr/bin/env python3
"""
TG Player - Database Maintenance & Album Enrichment Script

Fixes common database issues caused by legacy enrichment logic:
1. Resets false 'is_unavailable = 1' flags for tracks > 20MB and tracks with valid channel messages.
2. Deduplicates 'album_tracks' entries (removes redundant duplicate tracks on the same album position).
3. Enriches and fixes 'full_tracklist' from Deezer API for albums with missing or zero durations.
4. Resyncs 'track_number' positions in 'album_tracks' with official Deezer tracklists.

Usage:
    python scripts/cleanup_and_enrich_albums.py [--db tg_player.db] [--dry-run]
"""
import sys
import os
import json
import sqlite3
import urllib.request
import urllib.parse
import time
import argparse
import re
from typing import Optional, List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
except Exception:
    pass


def normalize_string(s: str) -> str:
    """Normalize string for fuzzy comparison"""
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r'[\(\[\{].*?[\)\]\}]', '', s)  # Remove bracketed info (prod, feat, etc.)
    s = re.sub(r'[^\w\s]', '', s)  # Remove punctuation
    return ' '.join(s.split())


def fetch_deezer_album(deezer_album_id: int) -> Optional[Dict[str, Any]]:
    """Fetch album information and tracks from Deezer API"""
    url = f"https://api.deezer.com/album/{deezer_album_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'TG-Player-Maintenance/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('error'):
                return None
            return data
    except Exception as e:
        print(f"    [Deezer API Error] album {deezer_album_id}: {e}")
        return None


def search_deezer_album(title: str, artist: str) -> Optional[int]:
    """Search for album on Deezer and return its ID if strong match"""
    query = f"{artist} {title}".strip()
    encoded = urllib.parse.quote(query)
    url = f"https://api.deezer.com/search/album?q={encoded}&limit=5"
    req = urllib.request.Request(url, headers={'User-Agent': 'TG-Player-Maintenance/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get('data', [])
            norm_title = normalize_string(title)
            for item in items:
                cand_title = normalize_string(item.get('title', ''))
                cand_artist = normalize_string(item.get('artist', {}).get('name', ''))
                if norm_title == cand_title or (cand_title and norm_title in cand_title):
                    return item.get('id')
    except Exception as e:
        print(f"    [Deezer Search Error] {query}: {e}")
    return None


def step1_fix_unavailable_tracks(con: sqlite3.Connection, dry_run: bool) -> int:
    """Reset false is_unavailable flags for large files and tracks with channel messages"""
    print("\n" + "="*60)
    print("STEP 1: Resetting false 'is_unavailable' flags")
    print("="*60)
    cur = con.cursor()
    
    # Query unavailable tracks
    unavail = cur.execute("""
        SELECT t.id, t.title, t.artist, t.file_size, cm.message_id
        FROM tracks t
        LEFT JOIN channel_messages cm ON cm.track_id = t.id AND cm.status = 'sent'
        WHERE t.is_unavailable = 1
    """).fetchall()
    
    print(f"Found {len(unavail)} currently unavailable tracks in database.")
    
    to_restore = []
    for t_id, title, artist, file_size, msg_id in unavail:
        is_large = file_size and file_size > 20 * 1024 * 1024
        has_msg = msg_id is not None
        if is_large or has_msg:
            reason = "File > 20MB" if is_large else "Valid channel message"
            to_restore.append((t_id, f"{artist} - {title}", reason))
    
    print(f"Identified {len(to_restore)} tracks to restore (not truly deleted).")
    for t_id, name, reason in to_restore[:10]:
        print(f"  - Track {t_id}: '{name}' ({reason})")
    if len(to_restore) > 10:
        print(f"  ... and {len(to_restore) - 10} more.")
        
    if not dry_run and to_restore:
        ids = [r[0] for r in to_restore]
        cur.executemany("UPDATE tracks SET is_unavailable = 0 WHERE id = ?", [(i,) for i in ids])
        con.commit()
        print(f"✅ Successfully restored {len(to_restore)} tracks to is_unavailable = 0.")
    elif dry_run:
        print(f"[DRY RUN] Would restore {len(to_restore)} tracks.")
        
    return len(to_restore)


def step2_deduplicate_album_tracks(con: sqlite3.Connection, dry_run: bool) -> int:
    """Remove duplicate tracks on the same album position, keeping the best one"""
    print("\n" + "="*60)
    print("STEP 2: Deduplicating 'album_tracks' positions")
    print("="*60)
    cur = con.cursor()
    
    # Find all (album_id, track_number) pairs with count > 1 (track_number > 0)
    dups = cur.execute("""
        SELECT album_id, track_number, count(*) as cnt
        FROM album_tracks
        WHERE track_number > 0
        GROUP BY album_id, track_number
        HAVING count(*) > 1
    """).fetchall()
    
    print(f"Found {len(dups)} duplicate position groups across albums.")
    
    deleted_at_ids = []
    
    for album_id, track_number, cnt in dups:
        # Get all entries for this position with track details
        rows = cur.execute("""
            SELECT at.id as at_id, at.track_id, t.is_unavailable, t.mime_type, t.file_size,
                   cm.message_id
            FROM album_tracks at
            JOIN tracks t ON t.id = at.track_id
            LEFT JOIN channel_messages cm ON cm.track_id = t.id AND cm.status = 'sent'
            WHERE at.album_id = ? AND at.track_number = ?
        """, (album_id, track_number)).fetchall()
        
        # Scoring function for choosing the best track:
        # 1. Available track: +1000
        # 2. In channel message: +500
        # 3. Streamable format (mp3/m4a/ogg): +200
        # 4. Valid file size (> 0): +50
        # 5. Newer track ID: +track_id (tie breaker)
        def score_row(r):
            at_id, track_id, is_unavail, mime_type, file_size, msg_id = r
            score = 0
            if not is_unavail:
                score += 1000
            if msg_id is not None:
                score += 500
            if mime_type and ('mpeg' in mime_type.lower() or 'mp4' in mime_type.lower() or 'ogg' in mime_type.lower()):
                score += 200
            if file_size and file_size > 0:
                score += 50
            score += track_id
            return score
            
        rows_sorted = sorted(rows, key=score_row, reverse=True)
        best = rows_sorted[0]
        to_delete = rows_sorted[1:]
        
        for r in to_delete:
            deleted_at_ids.append(r[0])
            
    print(f"Identified {len(deleted_at_ids)} redundant album_tracks rows to delete.")
    
    if not dry_run and deleted_at_ids:
        cur.executemany("DELETE FROM album_tracks WHERE id = ?", [(i,) for i in deleted_at_ids])
        con.commit()
        print(f"✅ Successfully deleted {len(deleted_at_ids)} duplicate album_tracks records.")
    elif dry_run:
        print(f"[DRY RUN] Would delete {len(deleted_at_ids)} duplicate album_tracks records.")
        
    return len(deleted_at_ids)


def step3_enrich_full_tracklists(con: sqlite3.Connection, dry_run: bool) -> int:
    """Enrich full_tracklist from Deezer for albums with missing or zero durations"""
    print("\n" + "="*60)
    print("STEP 3: Enriching 'full_tracklist' from Deezer API")
    print("="*60)
    cur = con.cursor()
    
    albums = cur.execute("""
        SELECT id, name, artist, total_tracks, full_tracklist, deezer_album_id
        FROM albums
        WHERE full_tracklist IS NOT NULL
    """).fetchall()
    
    albums_to_update = []
    for aid, name, artist, total_tracks, ft_raw, dz_id in albums:
        try:
            tl = json.loads(ft_raw)
            if not tl or any(not item.get('duration') or item.get('duration') == 0 for item in tl):
                albums_to_update.append((aid, name, artist, dz_id))
        except Exception:
            albums_to_update.append((aid, name, artist, dz_id))
            
    print(f"Found {len(albums_to_update)} albums with zero-duration tracks in full_tracklist.")
    
    updated_count = 0
    for aid, name, artist, dz_id in albums_to_update:
        # If no deezer_album_id, try to search Deezer
        if not dz_id:
            found_id = search_deezer_album(name, artist)
            time.sleep(0.1)
            if found_id:
                # Check if another album already has this deezer_album_id
                existing_album = cur.execute("SELECT id, name FROM albums WHERE deezer_album_id = ? AND id != ?", (found_id, aid)).fetchone()
                if existing_album:
                    print(f"    ⚠️ Deezer ID {found_id} already belongs to album {existing_album[0]} ('{existing_album[1]}'). Merging album {aid} into {existing_album[0]}...")
                    if not dry_run:
                        cur.execute("UPDATE OR IGNORE album_tracks SET album_id = ? WHERE album_id = ?", (existing_album[0], aid))
                        cur.execute("DELETE FROM album_tracks WHERE album_id = ?", (aid,))
                        cur.execute("DELETE FROM albums WHERE id = ?", (aid,))
                        con.commit()
                    continue
                else:
                    dz_id = found_id
                    if not dry_run:
                        try:
                            cur.execute("UPDATE albums SET deezer_album_id = ? WHERE id = ?", (dz_id, aid))
                            con.commit()
                        except sqlite3.IntegrityError:
                            continue
                
        if not dz_id:
            continue
            
        print(f"  Fetching Deezer album {dz_id} for '{name}' by '{artist}' (ID {aid})...")
        dz_data = fetch_deezer_album(dz_id)
        time.sleep(0.15)  # Rate limit politeness
        
        if not dz_data:
            continue
            
        tracks_data = dz_data.get('tracks', {}).get('data', [])
        if not tracks_data:
            continue
            
        new_tracklist = []
        for i, t in enumerate(tracks_data, 1):
            new_tracklist.append({
                "track_number": i,
                "title": t.get("title", ""),
                "artist": t.get("artist", {}).get("name", artist),
                "duration": t.get("duration", 0),
                "deezer_id": t.get("id"),
            })
            
        total_tr = len(new_tracklist)
        cover = dz_data.get("cover_big") or dz_data.get("cover_medium")
        release_date = dz_data.get("release_date")
        
        if not dry_run:
            cur.execute("""
                UPDATE albums 
                SET full_tracklist = ?, total_tracks = ?, cover_url = COALESCE(cover_url, ?), release_date = COALESCE(release_date, ?), updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(new_tracklist, ensure_ascii=False), total_tr, cover, release_date, aid))
            con.commit()
            updated_count += 1
            print(f"    ✅ Updated album {aid}: {len(new_tracklist)} tracks with exact durations.")
        else:
            updated_count += 1
            print(f"    [DRY RUN] Would update album {aid}: {len(new_tracklist)} tracks.")
            
    print(f"✅ Enriched {updated_count} albums with Deezer tracklists.")
    return updated_count


def step4_resync_album_tracks_positions(con: sqlite3.Connection, dry_run: bool) -> int:
    """Sync tracks in album_tracks with official full_tracklist positions"""
    print("\n" + "="*60)
    print("STEP 4: Resyncing 'album_tracks' positions with full_tracklist")
    print("="*60)
    cur = con.cursor()
    
    albums_with_ft = cur.execute("""
        SELECT id, name, artist, full_tracklist
        FROM albums
        WHERE full_tracklist IS NOT NULL
    """).fetchall()
    
    synced_count = 0
    for aid, name, artist, ft_raw in albums_with_ft:
        try:
            tl = json.loads(ft_raw)
            if not tl:
                continue
        except Exception:
            continue
            
        # Build lookup by normalized title
        title_to_pos = {}
        for item in tl:
            norm = normalize_string(item.get('title', ''))
            if norm:
                title_to_pos[norm] = item.get('track_number', 0)
                
        # Get tracks linked to this album
        ats = cur.execute("""
            SELECT at.id, at.track_id, at.track_number, t.title
            FROM album_tracks at
            JOIN tracks t ON t.id = at.track_id
            WHERE at.album_id = ?
        """, (aid,)).fetchall()
        
        for at_id, t_id, cur_pos, title in ats:
            norm_t = normalize_string(title or '')
            official_pos = title_to_pos.get(norm_t)
            if official_pos and official_pos > 0 and cur_pos != official_pos:
                if not dry_run:
                    cur.execute("UPDATE album_tracks SET track_number = ? WHERE id = ?", (official_pos, at_id))
                    synced_count += 1
                else:
                    synced_count += 1
                    
    if not dry_run and synced_count > 0:
        con.commit()
        print(f"✅ Resynced {synced_count} track positions in album_tracks.")
    elif dry_run:
        print(f"[DRY RUN] Would resync {synced_count} track positions in album_tracks.")
        
    return synced_count


def main():
    parser = argparse.ArgumentParser(description="TG Player Database Maintenance & Album Enrichment")
    parser.add_argument("--db", default="tg_player.db", help="Path to SQLite database file (default: tg_player.db)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without committing changes")
    args = parser.parse_args()
    
    db_path = args.db
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)
        
    print(f"Starting Database Maintenance on: {os.path.abspath(db_path)}")
    print(f"Dry run mode: {'ON (no changes will be made)' if args.dry_run else 'OFF (changes will be committed)'}")
    
    con = sqlite3.connect(db_path)
    try:
        step1_fix_unavailable_tracks(con, args.dry_run)
        step3_enrich_full_tracklists(con, args.dry_run)
        step4_resync_album_tracks_positions(con, args.dry_run)
        step2_deduplicate_album_tracks(con, args.dry_run)
        print("\n" + "="*60)
        print("🎉 MAINTENANCE COMPLETE!")
        print("="*60)
    finally:
        con.close()


if __name__ == "__main__":
    main()
