#!/usr/bin/env python3
"""
Cleanup script for TG Player - Find and remove problematic albums

Usage:
    python cleanup_album.py
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Load .env.local if exists
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
elif os.path.exists(".env"):
    load_dotenv(".env")

# Set dummy token if not configured (for cleanup script only)
if not os.getenv("BOT_TOKEN"):
    os.environ["BOT_TOKEN"] = "1234567890:ABCdefGHIjklmNOpqrsTUVwxyz"

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.models import Album, AlbumTrack, Track

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_album_by_name(album_name: str):
    """Find album by exact name"""
    async with get_session() as session:
        result = await session.execute(
            select(Album).where(Album.name == album_name)
        )
        return result.scalar_one_or_none()


async def get_album_tracks(album_id: int):
    """Get all tracks in album"""
    async with get_session() as session:
        result = await session.execute(
            select(AlbumTrack, Track)
            .join(Track)
            .where(AlbumTrack.album_id == album_id)
            .options(selectinload(AlbumTrack.track))
        )
        return result.all()


async def cleanup_album(album_name: str, auto_confirm: bool = False):
    """Find and cleanup problematic album"""
    
    # Case-insensitive search for album
    async with get_session() as session:
        # Search for album (case-insensitive)
        result = await session.execute(
            select(Album).where(
                func.lower(Album.name) == func.lower(album_name)
            )
        )
        album = result.scalar_one_or_none()
        
        if not album:
            logger.warning(f"Album '{album_name}' not found")
            return False
    
    logger.info(f"\n=== Found Album ===")
    logger.info(f"ID: {album.id}")
    logger.info(f"Name: {album.name}")
    logger.info(f"Artist: {album.artist}")
    logger.info(f"Normalized: {album.normalized_name} / {album.normalized_artist}")
    logger.info(f"Created: {album.created_at}")
    logger.info(f"Deezer ID: {album.deezer_album_id}")
    
    # Get tracks in this album
    async with get_session() as session:
        result = await session.execute(
            select(AlbumTrack, Track)
            .join(Track)
            .where(AlbumTrack.album_id == album.id)
            .options(selectinload(AlbumTrack.track))
        )
        album_tracks = result.all()
    
    logger.info(f"\n=== Tracks in Album ({len(album_tracks)}) ===")
    for at, track in album_tracks:
        logger.info(f"  ID {track.id}: '{track.title}' by {track.artist}")
    
    # Check if any track has placeholder title
    has_unknown_title = any(
        not at[1].title or at[1].title == "Без названия"
        for at in album_tracks
    )
    
    if has_unknown_title:
        logger.warning("\n⚠️  FOUND TRACKS WITHOUT TITLE - This is the issue!")
    
    # Ask for confirmation unless auto_confirm
    if not auto_confirm:
        # Check if we are in interactive terminal
        if not os.isatty(0):
            logger.info("Non-interactive terminal detected, auto-confirming deletion...")
        else:
            response = input(f"\n❓ Delete this album? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Cancelled")
                return False
    
    # Delete album (cascade will remove AlbumTrack entries)
    async with get_session() as session:
        album_to_delete = await session.get(Album, album.id)
        if album_to_delete:
            await session.delete(album_to_delete)
            await session.commit()
            logger.info(f"\n✅ Deleted album '{album_name}'")
    
    # Verify deletion
    async with get_session() as session:
        result = await session.execute(
            select(Album).where(Album.id == album.id)
        )
        deleted = result.scalar_one_or_none()
        
        if not deleted:
            logger.info("✅ Confirmed: Album removed from database")
            return True
        else:
            logger.error("❌ Album still exists!")
            return False


async def find_albums_with_unknown_tracks():
    """Find all albums that have tracks without titles"""
    logger.info("\n=== Scanning for albums with unknown-title tracks ===")
    
    async with get_session() as session:
        # Get all albums
        result = await session.execute(
            select(Album)
            .options(selectinload(Album.tracks).selectinload(AlbumTrack.track))
        )
        albums = result.scalars().all()
    
    problematic = []
    for album in albums:
        unknown_tracks = [
            at.track for at in album.tracks
            if not at.track.title or at.track.title == "Без названия"
        ]
        if unknown_tracks:
            problematic.append((album, unknown_tracks))
            logger.warning(
                f"\n⚠️  Album '{album.name}' has {len(unknown_tracks)} "
                f"track(s) without title"
            )
            for track in unknown_tracks:
                logger.warning(f"   - Track ID {track.id}: '{track.title}'")
    
    return problematic


async def main():
    """Main cleanup routine"""
    
    # First, scan all albums  
    problematic = await find_albums_with_unknown_tracks()
    
    if not problematic:
        logger.info("\n✅ No albums with unknown-title tracks found")
        return
    
    logger.info(f"\n Found {len(problematic)} problematic album(s)")
    
    # Cleanup the specific album
    target_album = "МЕЖДУ ДОБРОМ И ЗЛОМ"
    logger.info(f"\n=== Attempting to clean up '{target_album}' ===")
    await cleanup_album(target_album)
    
    # Re-scan to verify
    logger.info("\n=== Re-scanning after cleanup ===")
    remaining = await find_albums_with_unknown_tracks()
    
    if not remaining:
        logger.info("\n✅ All problematic albums have been removed!")
    else:
        logger.warning(f"\n⚠️  Still {len(remaining)} problematic album(s) found")


if __name__ == "__main__":
    asyncio.run(main())
