"""
TG Player - Database Cleanup for Bogus 'Likes' Albums and Track Enrichments

Finds and deletes pseudo-albums (e.g. 'meth (Likes)', 'Liked Songs') from `albums` and `album_tracks`,
clears bogus `album_name` in `track_enrichments`, and resets their `enrichment_status` to 'pending'
so the background enrichment worker can match them with their true albums via Deezer/Last.fm.
"""
import sys
import os
import sqlite3

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.matching import is_bogus_album_name

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tg_player.db"))


def run_cleanup():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return

    print(f"Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Inspect bogus albums in `albums` table
        cursor.execute("SELECT id, name, artist FROM albums")
        all_albums = cursor.fetchall()

        bogus_albums = [alb for alb in all_albums if is_bogus_album_name(alb[1])]
        print(f"\nFound {len(bogus_albums)} bogus album(s) in `albums`:")
        for alb_id, name, artist in bogus_albums:
            print(f"  [ID {alb_id}] '{name}' by '{artist}'")

        if bogus_albums:
            bogus_ids = [alb[0] for alb in bogus_albums]
            placeholders = ",".join("?" * len(bogus_ids))

            # Delete associations in album_tracks
            cursor.execute(
                f"DELETE FROM album_tracks WHERE album_id IN ({placeholders})",
                bogus_ids,
            )
            deleted_at_count = cursor.rowcount
            print(f"Removed {deleted_at_count} row(s) from `album_tracks`.")

            # Delete the albums
            cursor.execute(
                f"DELETE FROM albums WHERE id IN ({placeholders})",
                bogus_ids,
            )
            deleted_alb_count = cursor.rowcount
            print(f"Deleted {deleted_alb_count} bogus album(s) from `albums`.")

        # 2. Inspect bogus album_name in `track_enrichments`
        cursor.execute("SELECT track_id, album_name FROM track_enrichments WHERE album_name IS NOT NULL")
        all_enrichments = cursor.fetchall()

        bogus_enrichment_track_ids = [
            track_id for track_id, album_name in all_enrichments if is_bogus_album_name(album_name)
        ]
        print(f"\nFound {len(bogus_enrichment_track_ids)} track enrichment(s) with bogus album name.")

        if bogus_enrichment_track_ids:
            placeholders = ",".join("?" * len(bogus_enrichment_track_ids))

            # Clear album_name and deezer_album_id in track_enrichments
            cursor.execute(
                f"UPDATE track_enrichments SET album_name = NULL, deezer_album_id = NULL WHERE track_id IN ({placeholders})",
                bogus_enrichment_track_ids,
            )
            updated_te = cursor.rowcount
            print(f"Cleared album_name on {updated_te} record(s) in `track_enrichments`.")

            # Reset tracks to 'pending' enrichment status so enrichment worker can fetch real album
            cursor.execute(
                f"UPDATE tracks SET enrichment_status = 'pending' WHERE id IN ({placeholders})",
                bogus_enrichment_track_ids,
            )
            updated_tracks = cursor.rowcount
            print(f"Reset enrichment_status to 'pending' on {updated_tracks} track(s) in `tracks`.")

        conn.commit()
        print("\nCleanup successfully completed and committed to database.")

    except Exception as e:
        conn.rollback()
        print(f"\nError occurred during cleanup, transaction rolled back: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_cleanup()
