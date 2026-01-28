#!/usr/bin/env python3
"""
Debug script to check channel sync state.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from shared.database import get_session
from shared.models import UserChannel, ChannelMessage, Track, UserLibrary


async def check_sync_state(user_id: int = None):
    """Check sync state for a user or all users."""
    async with get_session() as session:
        # Get all channels
        if user_id:
            channels_result = await session.execute(
                select(UserChannel).where(UserChannel.user_id == user_id)
            )
        else:
            channels_result = await session.execute(select(UserChannel))
        
        channels = channels_result.scalars().all()
        
        if not channels:
            print("❌ No channels found")
            return
        
        for channel in channels:
            print(f"\n{'='*60}")
            print(f"📢 Channel: {channel.channel_title or 'Unknown'}")
            print(f"   User ID: {channel.user_id}")
            print(f"   Channel ID: {channel.channel_id}")
            print(f"   Active: {channel.is_active}")
            print(f"   Include hashtags: {channel.include_hashtags}")
            
            # Count messages in channel_messages table
            msg_count = await session.scalar(
                select(func.count(ChannelMessage.id)).where(
                    ChannelMessage.channel_id == channel.id
                )
            )
            print(f"\n   📊 Records in channel_messages: {msg_count}")
            
            # Count tracks in user's library
            library_count = await session.scalar(
                select(func.count(UserLibrary.id)).where(
                    UserLibrary.user_id == channel.user_id
                )
            )
            print(f"   📚 Tracks in user library: {library_count}")
            
            # Get synced track IDs
            synced_result = await session.execute(
                select(ChannelMessage.track_id).where(
                    ChannelMessage.channel_id == channel.id
                )
            )
            synced_track_ids = set(synced_result.scalars().all())
            print(f"   ✅ Unique synced track IDs: {len(synced_track_ids)}")
            
            # Check for duplicates in channel_messages
            dup_result = await session.execute(
                select(
                    ChannelMessage.track_id,
                    func.count(ChannelMessage.id).label('cnt')
                )
                .where(ChannelMessage.channel_id == channel.id)
                .group_by(ChannelMessage.track_id)
                .having(func.count(ChannelMessage.id) > 1)
            )
            duplicates = dup_result.all()
            if duplicates:
                print(f"   ⚠️ Duplicate entries: {len(duplicates)}")
                for track_id, cnt in duplicates[:5]:
                    track = await session.get(Track, track_id)
                    print(f"      - Track {track_id}: {track.title if track else 'Unknown'} ({cnt} copies)")
            else:
                print(f"   ✅ No duplicate entries in DB")
            
            # Calculate what should be synced
            library_result = await session.execute(
                select(UserLibrary.track_id).where(
                    UserLibrary.user_id == channel.user_id
                )
            )
            library_track_ids = set(library_result.scalars().all())
            
            not_synced = library_track_ids - synced_track_ids
            print(f"\n   📤 To sync (library - synced): {len(not_synced)}")
            
            # Show first few unsynced
            if not_synced and len(not_synced) <= 10:
                print("   Not synced track IDs:", list(not_synced)[:10])
            
            # Show last few synced messages
            if msg_count > 0:
                last_msgs = await session.execute(
                    select(ChannelMessage)
                    .where(ChannelMessage.channel_id == channel.id)
                    .order_by(ChannelMessage.id.desc())
                    .limit(5)
                )
                print(f"\n   📝 Last 5 synced messages:")
                for msg in last_msgs.scalars().all():
                    track = await session.get(Track, msg.track_id)
                    print(f"      - ID {msg.id}: msg_id={msg.message_id}, track={track.title if track else 'Unknown'}")


async def main():
    user_id = None
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
        except ValueError:
            pass
    
    print("🔍 Checking channel sync state...\n")
    await check_sync_state(user_id)


if __name__ == "__main__":
    asyncio.run(main())
