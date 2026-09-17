"""
Targeted cleanup script to purge mismatched albums and corrupted track enrichments.

Finds albums whose full_tracklist has 0% artist match with the album's artist
(e.g., Bladee matched to jet nine or Michelle Blades).
Clears the corrupted metadata and allows clean re-enrichment.
"""
import sys
import os
import sqlite3
import json
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from shared.matching import fuzzy_match_artist, ARTIST_MATCH_THRESHOLD, normalize_artist

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tg_player.db")


# Known bilingual artist equivalents and typos to preserve legitimate matches
KNOWN_ARTIST_ALIASES = {
    ('calvin harris', 'калвин харрис'),
    ('калвин харрис', 'calvin harris'),
    ('guf', 'гуф'),
    ('гуф', 'guf'),
    ('exicision', 'excision'),
    ('excision', 'exicision'),
    ('korn', 'koян'),
    ('koян', 'korn'),
    ('#####', '#####'),
    ('twenty one pilots stressed out', 'twenty one pilots'),
    ('twenty one pilots', 'twenty one pilots stressed out'),
    ('purity', 'purity filter'),
    ('purity filter', 'purity'),
    ('ghidemora', 'ghidemora archive'),
    ('ghidemora archive', 'ghidemora'),
}


def find_mismatched_albums(conn: sqlite3.Connection) -> List[Tuple[int, str, str, str, str, int]]:
    """Find all albums where full_tracklist has 0% artist match."""
    c = conn.cursor()
    c.execute(
        "SELECT id, name, artist, deezer_album_id, full_tracklist, cover_url "
        "FROM albums WHERE full_tracklist IS NOT NULL"
    )
    rows = c.fetchall()
    
    mismatched = []
    for aid, name, artist, deezer_id, ft_json, cover_url in rows:
        if not artist or artist.lower() in ('various artists', 'soundtrack', 'ost', 'va'):
            continue
        try:
            ft = json.loads(ft_json)
        except Exception:
            continue
        if not isinstance(ft, list) or not ft:
            continue
        
        norm_alb_artist = normalize_artist(artist)
        matches = []
        first_track_artist = ""
        for item in ft:
            track_artist = item.get('artist', '')
            if isinstance(track_artist, dict):
                track_artist = track_artist.get('name', '')
            if not first_track_artist:
                first_track_artist = str(track_artist)
            
            norm_trk_artist = normalize_artist(str(track_artist))
            
            # Check known aliases
            if (norm_alb_artist, norm_trk_artist) in KNOWN_ARTIST_ALIASES or (norm_trk_artist, norm_alb_artist) in KNOWN_ARTIST_ALIASES:
                score = 1.0
            else:
                score = fuzzy_match_artist(artist, str(track_artist))
            matches.append(score >= ARTIST_MATCH_THRESHOLD)
        
        match_rate = sum(matches) / len(matches) if matches else 0
        if match_rate == 0:
            c.execute("SELECT count(*) FROM album_tracks WHERE album_id = ?", (aid,))
            user_tracks_cnt = c.fetchone()[0]
            mismatched.append((aid, name, artist, deezer_id, first_track_artist, user_tracks_cnt))
            
    return mismatched


def purge_mismatched_albums(conn: sqlite3.Connection, dry_run: bool = True):
    mismatched = find_mismatched_albums(conn)
    print(f"Found {len(mismatched)} mismatched albums.")
    
    c = conn.cursor()
    cleared_albums = 0
    deleted_ghost_albums = 0
    cleaned_tracks = 0
    
    for aid, name, artist, deezer_id, first_trk_artist, user_tracks_cnt in mismatched:
        print(f"[{'DRY-RUN' if dry_run else 'APPLY'}] Album {aid}: '{name}' by '{artist}' (Deezer: {deezer_id}, Deezer artist: '{first_trk_artist}') | Tracks: {user_tracks_cnt}")
        
        if not dry_run:
            # 1. Clear album tracklist and bad Deezer link
            c.execute(
                "UPDATE albums SET full_tracklist = NULL, deezer_album_id = NULL, total_tracks = NULL, "
                "cover_url = CASE WHEN cover_url LIKE '%dzcdn.net%' THEN NULL ELSE cover_url END "
                "WHERE id = ?",
                (aid,)
            )
            cleared_albums += 1
            
            # 2. If album has no user tracks, delete it
            if user_tracks_cnt == 0:
                c.execute("DELETE FROM albums WHERE id = ?", (aid,))
                deleted_ghost_albums += 1
                
            # 3. Clean track enrichments that were hijacked by this corrupted deezer_album_id
            if deezer_id:
                c.execute(
                    "SELECT track_id FROM track_enrichments WHERE deezer_album_id = ?",
                    (deezer_id,)
                )
                affected_track_ids = [r[0] for r in c.fetchall()]
                if affected_track_ids:
                    # Clear bad album link and deezer track ID from enrichment, KEEP all Last.fm genre tags intact!
                    c.execute(
                        "UPDATE track_enrichments SET deezer_album_id = NULL, deezer_track_id = NULL, album_name = NULL, "
                        "cover_url = CASE WHEN cover_url LIKE '%dzcdn.net%' THEN NULL ELSE cover_url END "
                        "WHERE deezer_album_id = ?",
                        (deezer_id,)
                    )
                    cleaned_tracks += len(affected_track_ids)
                    
            # 4. For user tracks in this album, reset sequential track numbers (1, 2, 3...)
            c.execute("SELECT id FROM album_tracks WHERE album_id = ? ORDER BY id ASC", (aid,))
            at_rows = c.fetchall()
            for seq_idx, (at_id,) in enumerate(at_rows, start=1):
                c.execute("UPDATE album_tracks SET track_number = ? WHERE id = ?", (seq_idx, at_id))

    if not dry_run:
        conn.commit()
        print("\n[SUCCESS] Purge complete:")
        print(f"  - Albums cleared: {cleared_albums}")
        print(f"  - Ghost albums deleted: {deleted_ghost_albums}")
        print(f"  - Tracks cleaned of bad album links: {cleaned_tracks}")
    else:
        print("\n[DRY-RUN] No changes written to database.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply changes to database")
    args = parser.parse_args()
    
    conn = sqlite3.connect(DB_PATH)
    purge_mismatched_albums(conn, dry_run=not args.apply)
    conn.close()
