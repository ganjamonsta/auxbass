#!/usr/bin/env python3
"""
Retry failed enrichment for tracks.

Some tracks fail enrichment due to:
1. Rate limiting (API throttling)
2. Temporary network issues
3. Track not found on Deezer (this is normal for rare tracks)

This script resets failed tracks to pending for retry.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, func
from shared.database import get_session
from shared.models import Track


async def get_failed_stats():
    """Get statistics about failed tracks."""
    async with get_session() as session:
        # Count by status
        result = await session.execute(
            select(Track.enrichment_status, func.count(Track.id))
            .group_by(Track.enrichment_status)
        )
        stats = {row[0]: row[1] for row in result.all()}
        
        # Get sample of failed tracks
        result = await session.execute(
            select(Track)
            .where(Track.enrichment_status == "failed")
            .limit(20)
        )
        samples = result.scalars().all()
        
        return stats, samples


async def reset_failed_to_pending(limit: int = None):
    """Reset failed tracks to pending for retry."""
    async with get_session() as session:
        query = (
            update(Track)
            .where(Track.enrichment_status == "failed")
            .values(enrichment_status="pending")
        )
        
        if limit:
            # Get IDs to reset
            result = await session.execute(
                select(Track.id)
                .where(Track.enrichment_status == "failed")
                .limit(limit)
            )
            ids = [row[0] for row in result.all()]
            
            if ids:
                await session.execute(
                    update(Track)
                    .where(Track.id.in_(ids))
                    .values(enrichment_status="pending")
                )
                await session.commit()
                return len(ids)
            return 0
        else:
            result = await session.execute(query)
            await session.commit()
            return result.rowcount


async def main():
    print("=" * 60)
    print("RETRY FAILED ENRICHMENT")
    print("=" * 60)
    
    stats, samples = await get_failed_stats()
    
    print("\nEnrichment status:")
    for status, count in sorted(stats.items()):
        print(f"  {status}: {count}")
    
    failed_count = stats.get("failed", 0)
    
    if failed_count == 0:
        print("\n✓ No failed tracks!")
        return
    
    print(f"\nSample of failed tracks:")
    for track in samples:
        print(f"  - [{track.id}] {track.artist} - {track.title}")
    
    if len(samples) < failed_count:
        print(f"  ... and {failed_count - len(samples)} more")
    
    print(f"\nNote: Some tracks may genuinely not exist on Deezer.")
    print(f"      They will fail again, which is expected behavior.")
    
    # Options
    print(f"\nOptions:")
    print(f"  1. Reset ALL {failed_count} failed tracks to pending")
    print(f"  2. Reset only first 50 (for testing)")
    print(f"  3. Cancel")
    
    choice = input("\nChoice [1/2/3]: ").strip()
    
    if choice == "1":
        reset_count = await reset_failed_to_pending()
        print(f"\n✓ Reset {reset_count} tracks to pending")
    elif choice == "2":
        reset_count = await reset_failed_to_pending(limit=50)
        print(f"\n✓ Reset {reset_count} tracks to pending")
    else:
        print("\nCancelled.")
        return
    
    print(f"\nBot will retry enrichment automatically.")
    print(f"Check status with:")
    print(f'  sqlite3 /opt/tg_player/tg_player.db "SELECT enrichment_status, COUNT(*) FROM tracks GROUP BY enrichment_status;"')


if __name__ == "__main__":
    asyncio.run(main())
