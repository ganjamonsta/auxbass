#!/usr/bin/env python3
"""
Cleanup duplicate messages in user channels.

This script finds and removes duplicate track entries from channel_messages table
and optionally deletes duplicate messages from the Telegram channel.

Usage:
    python scripts/cleanup_channel_duplicates.py [--dry-run] [--delete-messages]

Options:
    --dry-run         Only show what would be deleted, don't actually delete
    --delete-messages Also delete duplicate messages from Telegram channel (requires bot)
"""
import asyncio
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete, func
from shared.database import get_session
from shared.models import UserChannel, ChannelMessage, Track


async def find_duplicates():
    """Find all duplicate track entries in channel_messages."""
    async with get_session() as session:
        # Find tracks that appear more than once per channel
        result = await session.execute(
            select(
                ChannelMessage.channel_id,
                ChannelMessage.track_id,
                func.count(ChannelMessage.id).label('count')
            )
            .group_by(ChannelMessage.channel_id, ChannelMessage.track_id)
            .having(func.count(ChannelMessage.id) > 1)
        )
        
        duplicates = []
        for row in result.all():
            channel_id, track_id, count = row
            
            # Get all message IDs for this duplicate
            msgs_result = await session.execute(
                select(ChannelMessage)
                .where(
                    ChannelMessage.channel_id == channel_id,
                    ChannelMessage.track_id == track_id
                )
                .order_by(ChannelMessage.id.asc())
            )
            messages = msgs_result.scalars().all()
            
            # Get channel info
            channel = await session.get(UserChannel, channel_id)
            
            # Get track info
            track = await session.get(Track, track_id)
            
            duplicates.append({
                'channel_id': channel_id,
                'channel_title': channel.channel_title if channel else 'Unknown',
                'telegram_channel_id': channel.channel_id if channel else None,
                'track_id': track_id,
                'track_title': f"{track.artist} - {track.title}" if track else 'Unknown',
                'count': count,
                'messages': messages,
                'keep_id': messages[0].id,  # Keep the first one
                'delete_ids': [m.id for m in messages[1:]],  # Delete the rest
                'delete_message_ids': [m.message_id for m in messages[1:]],  # Telegram msg IDs
            })
        
        return duplicates


async def cleanup_duplicates(dry_run=True, delete_messages=False):
    """Remove duplicate entries from database and optionally from Telegram."""
    duplicates = await find_duplicates()
    
    if not duplicates:
        print("✅ No duplicates found!")
        return
    
    print(f"\n🔍 Found {len(duplicates)} tracks with duplicates:\n")
    
    total_to_delete = 0
    for dup in duplicates:
        print(f"  📢 {dup['channel_title']}")
        print(f"     🎵 {dup['track_title']}")
        print(f"     📊 {dup['count']} copies (will delete {len(dup['delete_ids'])})")
        print(f"     🗑️ Message IDs to delete: {dup['delete_message_ids']}")
        print()
        total_to_delete += len(dup['delete_ids'])
    
    print(f"📊 Total duplicate records to delete: {total_to_delete}")
    
    if dry_run:
        print("\n⚠️ DRY RUN - no changes made. Use without --dry-run to delete.")
        return
    
    # Delete from database
    async with get_session() as session:
        deleted_db = 0
        for dup in duplicates:
            for msg_id in dup['delete_ids']:
                await session.execute(
                    delete(ChannelMessage).where(ChannelMessage.id == msg_id)
                )
                deleted_db += 1
        
        await session.commit()
        print(f"\n✅ Deleted {deleted_db} duplicate records from database")
    
    # Optionally delete from Telegram
    if delete_messages:
        print("\n🤖 Deleting messages from Telegram channels...")
        
        from shared.config import get_settings
        from aiogram import Bot
        
        settings = get_settings()
        bot = Bot(token=settings.bot_token)
        
        deleted_tg = 0
        failed_tg = 0
        
        try:
            for dup in duplicates:
                if not dup['telegram_channel_id']:
                    continue
                    
                for msg_id in dup['delete_message_ids']:
                    try:
                        await bot.delete_message(
                            chat_id=dup['telegram_channel_id'],
                            message_id=msg_id
                        )
                        deleted_tg += 1
                        await asyncio.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        print(f"  ⚠️ Failed to delete message {msg_id}: {e}")
                        failed_tg += 1
            
            print(f"✅ Deleted {deleted_tg} messages from Telegram")
            if failed_tg:
                print(f"⚠️ Failed to delete {failed_tg} messages")
        finally:
            await bot.session.close()


async def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    delete_messages = "--delete-messages" in sys.argv or "-d" in sys.argv
    
    print("🔄 Checking for duplicate channel messages...\n")
    
    await cleanup_duplicates(dry_run=dry_run, delete_messages=delete_messages)


if __name__ == "__main__":
    asyncio.run(main())
