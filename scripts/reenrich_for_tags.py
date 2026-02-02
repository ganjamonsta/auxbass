"""
TG Player - Re-enrichment Script for Tags

This script resets all enriched tracks to pending status
to re-enrich them with Last.fm tags.

Usage:
    # Dry run (just show what would be reset)
    python scripts/reenrich_for_tags.py --dry-run
    
    # Actually reset tracks
    python scripts/reenrich_for_tags.py
    
    # Reset only tracks without tags (incremental)
    python scripts/reenrich_for_tags.py --only-missing-tags
"""
import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, func
from shared.database import get_session
from shared.models import Track, TrackEnrichment, EnrichmentStatus


async def get_stats():
    """Get current enrichment statistics"""
    async with get_session() as session:
        # Count by status
        result = await session.execute(
            select(Track.enrichment_status, func.count(Track.id))
            .group_by(Track.enrichment_status)
        )
        status_counts = {
            status.value if isinstance(status, EnrichmentStatus) else str(status): count 
            for status, count in result.all()
        }
        
        # Count tracks with tags
        result = await session.execute(
            select(func.count(TrackEnrichment.id))
            .where(TrackEnrichment.tags.isnot(None))
        )
        with_tags = result.scalar() or 0
        
        # Count tracks without tags but with enrichment
        result = await session.execute(
            select(func.count(TrackEnrichment.id))
            .where(TrackEnrichment.tags.is_(None))
        )
        without_tags = result.scalar() or 0
        
        return {
            "status_counts": status_counts,
            "with_tags": with_tags,
            "without_tags": without_tags,
        }


async def reset_all_to_pending(dry_run: bool = True):
    """Reset all completed/failed tracks to pending for re-enrichment"""
    async with get_session() as session:
        # Count affected tracks
        result = await session.execute(
            select(func.count(Track.id))
            .where(Track.enrichment_status.in_([
                EnrichmentStatus.COMPLETED,
                EnrichmentStatus.FAILED,
            ]))
        )
        count = result.scalar() or 0
        
        if dry_run:
            print(f"[DRY RUN] Would reset {count} tracks to pending status")
            return count
        
        # Reset to pending
        await session.execute(
            update(Track)
            .where(Track.enrichment_status.in_([
                EnrichmentStatus.COMPLETED,
                EnrichmentStatus.FAILED,
            ]))
            .values(enrichment_status=EnrichmentStatus.PENDING)
        )
        
        print(f"✅ Reset {count} tracks to pending status")
        return count


async def reset_missing_tags_to_pending(dry_run: bool = True):
    """Reset only tracks without tags to pending"""
    async with get_session() as session:
        # Find tracks with enrichment but no tags
        result = await session.execute(
            select(func.count(Track.id))
            .join(TrackEnrichment, TrackEnrichment.track_id == Track.id)
            .where(Track.enrichment_status == EnrichmentStatus.COMPLETED)
            .where(TrackEnrichment.tags.is_(None))
        )
        count = result.scalar() or 0
        
        if dry_run:
            print(f"[DRY RUN] Would reset {count} tracks (missing tags) to pending status")
            return count
        
        # Get IDs of tracks to reset
        result = await session.execute(
            select(Track.id)
            .join(TrackEnrichment, TrackEnrichment.track_id == Track.id)
            .where(Track.enrichment_status == EnrichmentStatus.COMPLETED)
            .where(TrackEnrichment.tags.is_(None))
        )
        track_ids = [row[0] for row in result.all()]
        
        if track_ids:
            await session.execute(
                update(Track)
                .where(Track.id.in_(track_ids))
                .values(enrichment_status=EnrichmentStatus.PENDING)
            )
        
        print(f"✅ Reset {count} tracks (missing tags) to pending status")
        return count


async def main():
    parser = argparse.ArgumentParser(
        description="Re-enrich tracks with Last.fm tags"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--only-missing-tags",
        action="store_true",
        help="Only reset tracks that don't have tags yet"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("TG Player - Re-enrichment for Tags")
    print("=" * 60)
    
    # Show current stats
    print("\n📊 Current statistics:")
    stats = await get_stats()
    for status, count in stats["status_counts"].items():
        print(f"   {status}: {count}")
    print(f"\n   Tracks WITH tags: {stats['with_tags']}")
    print(f"   Tracks WITHOUT tags: {stats['without_tags']}")
    
    print("\n" + "-" * 60)
    
    if args.only_missing_tags:
        await reset_missing_tags_to_pending(dry_run=args.dry_run)
    else:
        await reset_all_to_pending(dry_run=args.dry_run)
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")
    else:
        print("\n🚀 The enrichment worker will process these tracks automatically")
        print("   Or restart the bot to start processing immediately")


if __name__ == "__main__":
    asyncio.run(main())
