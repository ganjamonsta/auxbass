"""
Script to re-enrich tracks that have album = title (likely singles that should be album tracks)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import get_session
from shared.models import Track
from sqlalchemy import select, func
from bot.services.metadata import metadata_service


async def find_suspicious_tracks():
    """Find tracks where album name = track title (likely wrong)"""
    async with get_session() as session:
        result = await session.execute(
            select(Track)
            .where(
                Track.album.isnot(None),
                Track.album != "",
                func.lower(Track.album) == func.lower(Track.title)
            )
        )
        return list(result.scalars().all())


async def re_enrich_track(track: Track) -> bool:
    """Re-enrich a single track with improved metadata search"""
    print(f"   🔍 Searching: {track.artist} - {track.title}")
    
    result = await metadata_service.search_deezer(track.title, track.artist)
    
    if not result:
        print(f"      ❌ No results found")
        return False
    
    new_album = result.get("album")
    if not new_album:
        print(f"      ❌ No album in result")
        return False
    
    # Check if we found a better album (not same as title)
    if new_album.lower().strip() == track.title.lower().strip():
        print(f"      ⚠️  Still got single: {new_album}")
        return False
    
    print(f"      ✅ Found album: {new_album}")
    
    async with get_session() as session:
        db_track = await session.get(Track, track.id)
        if db_track:
            db_track.album = new_album
            if result.get("cover_url") and not db_track.cover_url:
                db_track.cover_url = result["cover_url"]
            if result.get("album_id"):
                db_track.deezer_album_id = result["album_id"]
            await session.commit()
            return True
    
    return False


async def main():
    print("🔍 Finding tracks with album = title...")
    
    tracks = await find_suspicious_tracks()
    print(f"📊 Found {len(tracks)} suspicious tracks\n")
    
    if not tracks:
        print("✨ No suspicious tracks found!")
        return
    
    # Show list
    for track in tracks[:20]:
        print(f"   • {track.artist} - {track.title} (album: {track.album})")
    
    if len(tracks) > 20:
        print(f"   ... and {len(tracks) - 20} more")
    
    # Ask for confirmation
    print(f"\n⚠️  This will re-enrich {len(tracks)} tracks")
    confirm = input("Continue? [y/N]: ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled")
        return
    
    fixed = 0
    skipped = 0
    
    for i, track in enumerate(tracks, 1):
        print(f"\n[{i}/{len(tracks)}] {track.artist} - {track.title}")
        
        try:
            if await re_enrich_track(track):
                fixed += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"      ❌ Error: {e}")
            skipped += 1
    
    print(f"\n✨ Done! Fixed: {fixed}, Skipped: {skipped}")
    
    # Close metadata service session
    await metadata_service.close()
    
    # Rebuild albums after fixing
    if fixed > 0:
        print("\n🔄 Rebuilding albums...")
        from bot.services.albums import album_service
        
        async with get_session() as session:
            result = await session.execute(
                select(Track.user_id).distinct()
            )
            user_ids = [row[0] for row in result.all()]
        
        for user_id in user_ids:
            stats = await album_service.assemble_albums_for_user(user_id)
            print(f"   User {user_id}: created={stats['created']}, updated={stats['updated']}")


if __name__ == "__main__":
    asyncio.run(main())
