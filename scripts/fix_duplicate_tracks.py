"""
Fix duplicate tracks: when multiple track records point to the same audio content
(same file_size + title + artist + duration), keep the earliest one and reroute
all album_track references to it.
"""
import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tg_player.db")


def find_and_fix_duplicates(conn: sqlite3.Connection, dry_run: bool = True):
    c = conn.cursor()

    # Find tracks with identical (title, artist, duration, file_size) groups
    c.execute("""
        SELECT lower(title), lower(artist), duration, file_size,
               count(*) cnt, min(id) keep_id, group_concat(id) all_ids
        FROM tracks
        WHERE title IS NOT NULL AND artist IS NOT NULL AND duration > 0 AND file_size > 0
        GROUP BY lower(title), lower(artist), duration, file_size
        HAVING count(*) > 1
    """)
    dup_groups = c.fetchall()

    print(f"Found {len(dup_groups)} groups of duplicate tracks")
    total_remapped = 0
    total_deleted = 0

    for norm_title, norm_artist, dur, fsize, cnt, keep_id, all_ids_str in dup_groups:
        all_ids = [int(x) for x in all_ids_str.split(',')]
        dup_ids = [x for x in all_ids if x != keep_id]
        print(f"\nDuplicate: '{norm_title}' by '{norm_artist}' ({dur}s, {fsize}b)")
        print(f"  Keep: {keep_id} | Duplicates: {dup_ids}")

        if not dry_run:
            for dup_id in dup_ids:
                # Re-point album_tracks references
                c.execute("SELECT id, album_id, track_number FROM album_tracks WHERE track_id = ?", (dup_id,))
                at_rows = c.fetchall()
                for at_id, album_id, track_num in at_rows:
                    # Check if keep_id already has an album_tracks entry for this album
                    c.execute("SELECT id FROM album_tracks WHERE track_id = ? AND album_id = ?", (keep_id, album_id))
                    existing = c.fetchone()
                    if existing:
                        # Delete duplicate album_tracks row
                        c.execute("DELETE FROM album_tracks WHERE id = ?", (at_id,))
                        print(f"  Deleted duplicate album_tracks row {at_id}")
                    else:
                        # Remap to keep_id
                        c.execute("UPDATE album_tracks SET track_id = ? WHERE id = ?", (keep_id, at_id))
                        print(f"  Remapped album_tracks row {at_id} -> track {keep_id}")
                    total_remapped += 1

                # Merge track_enrichments if dup_id has useful data
                c.execute("SELECT track_id, tags, genre, cover_url, lastfm_url FROM track_enrichments WHERE track_id = ?", (dup_id,))
                dup_enrich = c.fetchone()
                c.execute("SELECT track_id, tags, genre, cover_url, lastfm_url FROM track_enrichments WHERE track_id = ?", (keep_id,))
                keep_enrich = c.fetchone()

                if dup_enrich and not keep_enrich:
                    # Remap enrichment to keep_id
                    c.execute("UPDATE track_enrichments SET track_id = ? WHERE track_id = ?", (keep_id, dup_id))
                    print(f"  Remapped enrichment from {dup_id} to {keep_id}")
                elif dup_enrich and keep_enrich:
                    # Merge tags if keep has none
                    if not keep_enrich[1] and dup_enrich[1]:
                        c.execute("UPDATE track_enrichments SET tags = ? WHERE track_id = ?", (dup_enrich[1], keep_id))
                    if not keep_enrich[2] and dup_enrich[2]:
                        c.execute("UPDATE track_enrichments SET genre = ? WHERE track_id = ?", (dup_enrich[2], keep_id))
                    c.execute("DELETE FROM track_enrichments WHERE track_id = ?", (dup_id,))

                # Delete playlist entries for dup
                c.execute("DELETE FROM playlist_tracks WHERE track_id = ?", (dup_id,))
                # Delete user library entries for dup (keep_id already has the entry)
                c.execute("DELETE FROM user_library WHERE track_id = ?", (dup_id,))
                # Finally delete the duplicate track itself
                c.execute("DELETE FROM tracks WHERE id = ?", (dup_id,))
                total_deleted += 1

    if not dry_run:
        conn.commit()
        print(f"\n[SUCCESS] Fixed {total_remapped} album_tracks refs, deleted {total_deleted} duplicate tracks.")
    else:
        print("\n[DRY-RUN] No changes made.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    find_and_fix_duplicates(conn, dry_run=not args.apply)
    conn.close()
