#!/usr/bin/env python3
"""
TG Player - Channel Service Test Script

This script helps test and debug channel functionality:
1. Check if channel service is properly initialized
2. Test database connection and UserChannel model
3. List configured user channels
4. Verify bot access to a channel
5. Test track forwarding (dry-run mode available)

Usage:
    python scripts/test_channels.py [command] [args]

Commands:
    list                    List all configured user channels
    check <user_id>         Check channel config for a user
    verify <channel_id>     Verify bot can post to channel (requires bot running)
    stats                   Show channel statistics
    test_forward <user_id> <track_id>  Test forward (dry-run, no actual send)
    cleanup                 Remove inactive channels
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from shared.database import get_session, init_db
from shared.models import UserChannel, ChannelMessage, Track, User


async def list_channels():
    """List all configured user channels"""
    await init_db()
    
    async with get_session() as session:
        result = await session.execute(
            select(UserChannel, User)
            .join(User, UserChannel.user_id == User.id)
            .order_by(UserChannel.created_at.desc())
        )
        channels = result.all()
        
        if not channels:
            print("📭 No channels configured")
            return
        
        print(f"📢 Found {len(channels)} channel(s):\n")
        
        for channel, user in channels:
            # Get message count
            msg_count = await session.scalar(
                select(func.count(ChannelMessage.id)).where(
                    ChannelMessage.channel_id == channel.id
                )
            )
            
            status = "✅ Active" if channel.is_active else "❌ Inactive"
            auto = "📤 Auto-forward" if channel.auto_forward else "⏸️ Manual"
            tags = "🏷️ Hashtags" if channel.include_hashtags else "📝 No tags"
            
            print(f"═══════════════════════════════════════")
            print(f"👤 User: {user.first_name} (@{user.username or 'N/A'}) [ID: {user.id}]")
            print(f"📢 Channel: {channel.channel_title or 'Untitled'}")
            print(f"   ID: {channel.channel_id}")
            print(f"   Username: @{channel.channel_username or 'N/A'}")
            print(f"   Status: {status} | {auto} | {tags}")
            print(f"   Messages: {msg_count}")
            print(f"   Created: {channel.created_at}")
            print(f"   Updated: {channel.updated_at}")


async def check_user_channel(user_id: int):
    """Check channel configuration for a specific user"""
    await init_db()
    
    async with get_session() as session:
        # Get user
        user = await session.get(User, user_id)
        if not user:
            print(f"❌ User {user_id} not found in database")
            return
        
        print(f"👤 User: {user.first_name} (@{user.username or 'N/A'})")
        
        # Get channel
        channel = await session.scalar(
            select(UserChannel).where(UserChannel.user_id == user_id)
        )
        
        if not channel:
            print("❌ No channel configured for this user")
            return
        
        # Get message count
        msg_count = await session.scalar(
            select(func.count(ChannelMessage.id)).where(
                ChannelMessage.channel_id == channel.id
            )
        )
        
        # Get last 5 messages
        result = await session.execute(
            select(ChannelMessage, Track)
            .join(Track, ChannelMessage.track_id == Track.id)
            .where(ChannelMessage.channel_id == channel.id)
            .order_by(ChannelMessage.created_at.desc())
            .limit(5)
        )
        recent_messages = result.all()
        
        print(f"\n📢 Channel Configuration:")
        print(f"   Title: {channel.channel_title}")
        print(f"   ID: {channel.channel_id}")
        print(f"   Username: @{channel.channel_username or 'N/A'}")
        print(f"   Active: {channel.is_active}")
        print(f"   Auto-forward: {channel.auto_forward}")
        print(f"   Include hashtags: {channel.include_hashtags}")
        print(f"   Total messages: {msg_count}")
        
        if recent_messages:
            print(f"\n📜 Recent messages (last 5):")
            for msg, track in recent_messages:
                print(f"   🎵 {track.title or 'Untitled'} - {track.artist or 'Unknown'}")
                print(f"      Message ID: {msg.message_id}, Created: {msg.created_at}")


async def show_stats():
    """Show overall channel statistics"""
    await init_db()
    
    async with get_session() as session:
        # Total channels
        total_channels = await session.scalar(
            select(func.count(UserChannel.id))
        )
        
        # Active channels
        active_channels = await session.scalar(
            select(func.count(UserChannel.id)).where(UserChannel.is_active == True)
        )
        
        # Total messages
        total_messages = await session.scalar(
            select(func.count(ChannelMessage.id))
        )
        
        # Channels with messages
        channels_with_messages = await session.scalar(
            select(func.count(func.distinct(ChannelMessage.channel_id)))
        )
        
        print("📊 Channel Statistics")
        print("═" * 40)
        print(f"📢 Total channels: {total_channels}")
        print(f"✅ Active channels: {active_channels}")
        print(f"❌ Inactive channels: {total_channels - active_channels}")
        print(f"💬 Total messages: {total_messages}")
        print(f"📤 Channels with messages: {channels_with_messages}")
        
        if total_messages > 0:
            avg = total_messages / max(channels_with_messages, 1)
            print(f"📈 Avg messages per active channel: {avg:.1f}")


async def test_forward_dry_run(user_id: int, track_id: int):
    """Test what would happen if we forward a track (dry-run)"""
    await init_db()
    
    async with get_session() as session:
        # Get user
        user = await session.get(User, user_id)
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        # Get channel
        channel = await session.scalar(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.is_active == True
            )
        )
        
        if not channel:
            print(f"❌ No active channel for user {user_id}")
            return
        
        if not channel.auto_forward:
            print(f"⏸️ Auto-forward is disabled for this channel")
            return
        
        # Get track
        track = await session.get(Track, track_id)
        if not track:
            print(f"❌ Track {track_id} not found")
            return
        
        # Simulate hashtag generation
        from shared.matching import generate_hashtags, format_hashtags
        
        hashtags = []
        if channel.include_hashtags:
            hashtags = generate_hashtags(
                artist=track.artist,
                title=track.title,
                album=track.enrichment.album_name if track.enrichment else None,
                genre=track.enrichment.genre if track.enrichment else None,
            )
        
        # Build caption
        caption_parts = []
        if track.title:
            caption_parts.append(f"🎵 {track.title}")
        if track.artist:
            caption_parts.append(f"👤 {track.artist}")
        
        if hashtags:
            caption_parts.append("")
            caption_parts.append(format_hashtags(hashtags))
        
        caption = "\n".join(caption_parts)
        
        print("🔄 DRY-RUN: Forward simulation")
        print("═" * 40)
        print(f"👤 User: {user.first_name}")
        print(f"📢 Channel: {channel.channel_title} ({channel.channel_id})")
        print(f"🎵 Track: {track.title} - {track.artist}")
        print(f"📎 File ID: {track.file_id[:50]}...")
        print(f"\n📝 Caption that would be sent:")
        print("─" * 40)
        print(caption)
        print("─" * 40)
        print(f"\n✅ Forward would succeed (if bot has channel access)")


async def cleanup_inactive():
    """Remove channels that have been inactive for a long time"""
    await init_db()
    
    async with get_session() as session:
        result = await session.execute(
            select(UserChannel).where(UserChannel.is_active == False)
        )
        inactive = result.scalars().all()
        
        if not inactive:
            print("✅ No inactive channels to clean up")
            return
        
        print(f"Found {len(inactive)} inactive channel(s):")
        for ch in inactive:
            print(f"  - Channel {ch.channel_id} (user {ch.user_id}), updated: {ch.updated_at}")
        
        print("\n⚠️ This is a preview. To actually delete, uncomment the delete code.")
        # Uncomment to actually delete:
        # for ch in inactive:
        #     await session.delete(ch)
        # await session.commit()
        # print(f"✅ Deleted {len(inactive)} inactive channels")


def print_usage():
    """Print usage information"""
    print(__doc__)


async def main():
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        await list_channels()
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("Usage: test_channels.py check <user_id>")
            return
        user_id = int(sys.argv[2])
        await check_user_channel(user_id)
    
    elif command == "stats":
        await show_stats()
    
    elif command == "test_forward":
        if len(sys.argv) < 4:
            print("Usage: test_channels.py test_forward <user_id> <track_id>")
            return
        user_id = int(sys.argv[2])
        track_id = int(sys.argv[3])
        await test_forward_dry_run(user_id, track_id)
    
    elif command == "cleanup":
        await cleanup_inactive()
    
    elif command == "verify":
        print("⚠️ Channel verification requires running bot instance.")
        print("Use the bot /channel command to verify access interactively.")
    
    else:
        print(f"Unknown command: {command}")
        print_usage()


if __name__ == "__main__":
    asyncio.run(main())
