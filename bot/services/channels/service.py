"""
TG Player - User Channel Service

Handles backup of user's music library to their Telegram channel.
Features:
- Forward tracks to user's channel
- Generate hashtags for easy searching
- Update messages when enrichment completes
"""
from typing import Optional, List
from datetime import datetime
import json
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models import (
    UserChannel, ChannelMessage, Track, TrackEnrichment
)
from shared.matching import generate_hashtags, format_hashtags
from shared.database import get_session

logger = logging.getLogger(__name__)


class ChannelService:
    """Service for managing user channels and messages"""
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self._cancel_sync: dict[int, bool] = {}  # user_id -> cancel flag
        self._active_sync: dict[int, dict] = {}  # user_id -> sync status info
    
    def set_bot(self, bot: Bot):
        """Set bot instance for sending messages"""
        self.bot = bot
    
    def request_cancel_sync(self, user_id: int):
        """Request cancellation of ongoing sync for user"""
        self._cancel_sync[user_id] = True
    
    def is_sync_cancelled(self, user_id: int) -> bool:
        """Check if sync is cancelled for user"""
        return self._cancel_sync.get(user_id, False)
    
    def clear_cancel_flag(self, user_id: int):
        """Clear cancel flag for user"""
        self._cancel_sync.pop(user_id, None)
    
    def is_sync_active(self, user_id: int) -> bool:
        """Check if sync is currently running for user"""
        return user_id in self._active_sync
    
    def get_sync_status(self, user_id: int) -> Optional[dict]:
        """Get current sync status for user"""
        return self._active_sync.get(user_id)
    
    def _update_sync_status(self, user_id: int, current: int, total: int, synced: int):
        """Update sync status for user"""
        self._active_sync[user_id] = {
            "current": current,
            "total": total,
            "synced": synced
        }
    
    def _clear_sync_status(self, user_id: int):
        """Clear sync status for user"""
        self._active_sync.pop(user_id, None)
    
    async def setup_channel(
        self,
        user_id: int,
        channel_id: int,
        channel_username: Optional[str] = None,
        channel_title: Optional[str] = None,
        bot: Optional[Bot] = None,
    ) -> Optional[UserChannel]:
        """
        Setup or update user's channel for library backup.
        Verifies bot has access before saving.
        
        Args:
            user_id: Telegram user ID
            channel_id: Telegram channel ID (negative number)
            channel_username: Channel @username (optional)
            channel_title: Channel title (optional)
            bot: Bot instance for verification
        
        Returns:
            UserChannel object if successful, None if verification failed
        """
        use_bot = bot or self.bot
        if not use_bot:
            logger.error("No bot instance available for channel setup")
            return None
        
        # Verify access first
        success, title, error = await self.verify_channel_access(channel_id, use_bot)
        if not success:
            logger.warning(f"Channel verification failed for {channel_id}: {error}")
            return None
        
        # Use title from verification if not provided
        if not channel_title and title:
            channel_title = title
        
        async with get_session() as session:
            # Check if user already has a channel
            existing = await session.scalar(
                select(UserChannel).where(UserChannel.user_id == user_id)
            )
            
            if existing:
                # Update existing
                existing.channel_id = channel_id
                existing.channel_username = channel_username
                existing.channel_title = channel_title
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
                logger.info(f"Channel updated for user {user_id}: {channel_id}")
                return existing
            
            # Create new
            channel = UserChannel(
                user_id=user_id,
                channel_id=channel_id,
                channel_username=channel_username,
                channel_title=channel_title,
            )
            session.add(channel)
            await session.flush()
            
            logger.info(f"Channel setup for user {user_id}: {channel_id}")
            return channel
    
    async def get_user_channel(
        self,
        user_id: int
    ) -> Optional[UserChannel]:
        """Get user's channel if configured"""
        async with get_session() as session:
            channel = await session.scalar(
                select(UserChannel).where(
                    UserChannel.user_id == user_id,
                    UserChannel.is_active == True
                )
            )
            if channel:
                # Eagerly load message count
                count = await session.scalar(
                    select(func.count(ChannelMessage.id)).where(
                        ChannelMessage.channel_id == channel.id
                    )
                )
                # Add as dynamic attribute
                channel._message_count = count
            return channel
    
    @property
    def message_count(self):
        """Get message count - for use with UserChannel object"""
        return getattr(self, '_message_count', 0)
    
    async def get_channel_message_count(self, user_id: int) -> int:
        """Get count of messages in user's channel"""
        async with get_session() as session:
            channel = await session.scalar(
                select(UserChannel).where(
                    UserChannel.user_id == user_id,
                    UserChannel.is_active == True
                )
            )
            if not channel:
                return 0
            
            count = await session.scalar(
                select(func.count(ChannelMessage.id)).where(
                    ChannelMessage.channel_id == channel.id
                )
            )
            return count or 0
    
    async def get_sync_stats(self, user_id: int) -> dict:
        """
        Get sync statistics before starting sync.
        
        Returns:
            Dict with: total_tracks, already_synced, to_sync
        """
        async with get_session() as session:
            channel = await session.scalar(
                select(UserChannel).where(
                    UserChannel.user_id == user_id,
                    UserChannel.is_active == True
                )
            )
            
            if not channel:
                return {"total_tracks": 0, "already_synced": 0, "to_sync": 0, "error": "No channel"}
            
            # Count total tracks in library
            from shared.models import UserLibrary
            total = await session.scalar(
                select(func.count(UserLibrary.id)).where(
                    UserLibrary.user_id == user_id
                )
            ) or 0
            
            # Count already synced
            already_synced = await session.scalar(
                select(func.count(ChannelMessage.id)).where(
                    ChannelMessage.channel_id == channel.id
                )
            ) or 0
            
            return {
                "total_tracks": total,
                "already_synced": already_synced,
                "to_sync": max(0, total - already_synced),
                "channel_title": channel.channel_title or "Канал"
            }
    
    async def disable_channel(
        self,
        user_id: int
    ) -> bool:
        """Disable user's channel (don't delete, just deactivate)"""
        async with get_session() as session:
            channel = await session.scalar(
                select(UserChannel).where(UserChannel.user_id == user_id)
            )
            
            if channel:
                channel.is_active = False
                channel.updated_at = datetime.utcnow()
                return True
            
            return False
    
    async def forward_track_to_channel(
        self,
        user_id: int,
        track_id: int,
        bot: Optional[Bot] = None,
    ) -> bool:
        """
        Forward a track to user's channel with hashtags.
        
        Args:
            user_id: User who owns the channel
            track_id: Track ID to forward
            bot: Bot instance for sending
        
        Returns:
            True if forwarded successfully, False otherwise
        """
        use_bot = bot or self.bot
        if not use_bot:
            logger.error("No bot instance available for forwarding")
            return False
        
        async with get_session() as session:
            # Get channel
            channel = await session.scalar(
                select(UserChannel).where(
                    UserChannel.user_id == user_id,
                    UserChannel.is_active == True
                )
            )
            
            if not channel or not channel.auto_forward:
                return False
            
            # Get track with enrichment (eager load)
            result = await session.execute(
                select(Track)
                .options(selectinload(Track.enrichment))
                .where(Track.id == track_id)
            )
            track = result.scalar_one_or_none()
            if not track:
                return False
            
            try:
                # Generate hashtags
                hashtags = []
                if channel.include_hashtags:
                    enrichment = track.enrichment
                    hashtags = generate_hashtags(
                        artist=track.artist,
                        title=track.title,
                        album=enrichment.album_name if enrichment else None,
                        genre=enrichment.genre if enrichment else None,
                    )
                
                # Build caption
                caption_parts = []
                if track.title:
                    caption_parts.append(f"🎵 {track.title}")
                if track.artist:
                    caption_parts.append(f"👤 {track.artist}")
                if track.enrichment and track.enrichment.album_name:
                    caption_parts.append(f"💿 {track.enrichment.album_name}")
                
                if hashtags:
                    caption_parts.append("")
                    caption_parts.append(format_hashtags(hashtags))
                
                caption = "\n".join(caption_parts) if caption_parts else None
                
                # Forward the audio
                sent_message = await use_bot.send_audio(
                    chat_id=channel.channel_id,
                    audio=track.file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
                
                # Save message record
                channel_message = ChannelMessage(
                    channel_id=channel.id,
                    track_id=track.id,
                    message_id=sent_message.message_id,
                    hashtags=json.dumps(hashtags) if hashtags else None,
                )
                session.add(channel_message)
                await session.flush()
                
                logger.info(f"Track {track_id} forwarded to channel {channel.channel_id}")
                return True
                
            except TelegramForbiddenError:
                # Bot was removed from channel
                logger.warning(f"Bot removed from channel {channel.channel_id}, disabling")
                channel.is_active = False
                return False
                
            except TelegramBadRequest as e:
                logger.error(f"Failed to forward to channel: {e}")
                return False
    
    async def update_channel_message(
        self,
        track_id: int,
        bot: Optional[Bot] = None,
    ) -> int:
        """
        Update all channel messages for a track (after enrichment).
        Updates hashtags based on new metadata.
        
        Returns:
            Number of messages updated
        """
        use_bot = bot or self.bot
        if not use_bot:
            logger.error("No bot instance available for updating messages")
            return 0
        
        async with get_session() as session:
            # Get track with enrichment (eager load)
            result = await session.execute(
                select(Track)
                .options(selectinload(Track.enrichment))
                .where(Track.id == track_id)
            )
            track = result.scalar_one_or_none()
            if not track:
                return 0
            
            # Get all channel messages for this track
            result = await session.execute(
                select(ChannelMessage)
                .join(UserChannel)
                .where(
                    ChannelMessage.track_id == track_id,
                    UserChannel.is_active == True,
                    UserChannel.include_hashtags == True,
                )
            )
            messages = result.scalars().all()
            
            updated = 0
            for msg in messages:
                channel = await session.get(UserChannel, msg.channel_id)
                if not channel:
                    continue
                
                # Generate new hashtags
                new_hashtags = generate_hashtags(
                    artist=track.artist,
                    title=track.title,
                    album=track.enrichment.album_name if track.enrichment else None,
                    genre=track.enrichment.genre if track.enrichment else None,
                )
                
                # Build new caption
                caption_parts = []
                if track.title:
                    caption_parts.append(f"🎵 {track.title}")
                if track.artist:
                    caption_parts.append(f"👤 {track.artist}")
                if track.enrichment and track.enrichment.album_name:
                    caption_parts.append(f"💿 {track.enrichment.album_name}")
                
                if new_hashtags:
                    caption_parts.append("")
                    caption_parts.append(format_hashtags(new_hashtags))
                
                caption = "\n".join(caption_parts)
                
                try:
                    await use_bot.edit_message_caption(
                        chat_id=channel.channel_id,
                        message_id=msg.message_id,
                        caption=caption,
                        parse_mode="HTML",
                    )
                    
                    msg.hashtags = json.dumps(new_hashtags)
                    msg.updated_at = datetime.utcnow()
                    updated += 1
                    
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        pass  # Same content, skip
                    else:
                        logger.error(f"Failed to update message: {e}")
                except TelegramForbiddenError:
                    # Channel access lost
                    channel.is_active = False
        
            logger.info(f"Updated {updated} channel messages for track {track_id}")
            return updated
    
    async def sync_all_tracks(
        self,
        user_id: int,
        bot: Optional[Bot] = None,
        progress_callback=None,
    ) -> dict:
        """
        Sync all user's library tracks to their channel.
        Only sends tracks that haven't been sent yet.
        
        Args:
            user_id: User ID
            bot: Bot instance
            progress_callback: Optional async callback(current, total) for progress updates
        
        Returns:
            Dict with sync results: {synced, skipped, failed, total}
        """
        use_bot = bot or self.bot
        if not use_bot:
            logger.error("No bot instance available for sync")
            return {"synced": 0, "skipped": 0, "failed": 0, "total": 0}
        
        async with get_session() as session:
            # Get channel
            channel = await session.scalar(
                select(UserChannel).where(
                    UserChannel.user_id == user_id,
                    UserChannel.is_active == True
                )
            )
            
            if not channel:
                return {"synced": 0, "skipped": 0, "failed": 0, "total": 0, "error": "No channel"}
            
            # Get all user's tracks from library with enrichment
            from shared.models import UserLibrary
            result = await session.execute(
                select(Track)
                .options(selectinload(Track.enrichment))
                .join(UserLibrary, UserLibrary.track_id == Track.id)
                .where(UserLibrary.user_id == user_id)
                .order_by(UserLibrary.added_at.asc())
            )
            tracks = result.scalars().all()
            
            # Get already synced track IDs
            synced_result = await session.execute(
                select(ChannelMessage.track_id).where(
                    ChannelMessage.channel_id == channel.id
                )
            )
            synced_track_ids = set(synced_result.scalars().all())
            
            stats = {"synced": 0, "skipped": 0, "failed": 0, "total": len(tracks), "cancelled": False}
            
            # Calculate tracks to sync
            to_sync_count = len([t for t in tracks if t.id not in synced_track_ids])
            
            # Clear any previous cancel flag and set active sync
            self.clear_cancel_flag(user_id)
            self._update_sync_status(user_id, 0, to_sync_count, 0)
            
            try:
                sent_count = 0  # Actual sent counter for progress
                
                for i, track in enumerate(tracks):
                    # Check for cancellation
                    if self.is_sync_cancelled(user_id):
                        stats["cancelled"] = True
                        self.clear_cancel_flag(user_id)
                        break
                    
                    # Skip already synced
                    if track.id in synced_track_ids:
                        stats["skipped"] += 1
                        continue
                    
                    # Update sync status and call progress callback BEFORE sending
                    self._update_sync_status(user_id, sent_count, to_sync_count, stats["synced"])
                    if progress_callback:
                        try:
                            await progress_callback(sent_count, to_sync_count, stats["synced"])
                        except:
                            pass
                    
                    try:
                        # Generate hashtags
                        hashtags = []
                        if channel.include_hashtags:
                            enrichment = track.enrichment
                            hashtags = generate_hashtags(
                                artist=track.artist,
                                title=track.title,
                                album=enrichment.album_name if enrichment else None,
                                genre=enrichment.genre if enrichment else None,
                            )
                        
                        # Build caption
                        caption_parts = []
                        if track.title:
                            caption_parts.append(f"🎵 {track.title}")
                        if track.artist:
                            caption_parts.append(f"👤 {track.artist}")
                        if track.enrichment and track.enrichment.album_name:
                            caption_parts.append(f"💿 {track.enrichment.album_name}")
                        
                        if hashtags:
                            caption_parts.append("")
                            caption_parts.append(format_hashtags(hashtags))
                        
                        caption = "\n".join(caption_parts) if caption_parts else None
                        
                        # Send audio
                        sent_message = await use_bot.send_audio(
                            chat_id=channel.channel_id,
                            audio=track.file_id,
                            caption=caption,
                            parse_mode="HTML",
                        )
                        
                        # Save message record
                        channel_message = ChannelMessage(
                            channel_id=channel.id,
                            track_id=track.id,
                            message_id=sent_message.message_id,
                            hashtags=json.dumps(hashtags) if hashtags else None,
                        )
                        session.add(channel_message)
                        
                        stats["synced"] += 1
                        sent_count += 1
                        
                        # Delay to avoid rate limiting (Telegram allows ~20 msg/min to channels)
                        await asyncio.sleep(3)
                        
                    except TelegramRetryAfter as e:
                        # Rate limited - wait and retry
                        logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
                        await asyncio.sleep(e.retry_after + 1)
                        # Don't count as failed, will be retried on next sync
                        sent_count += 1
                        continue
                        
                    except TelegramForbiddenError:
                        channel.is_active = False
                        stats["failed"] += 1
                        break  # Stop sync if access lost
                        
                    except TelegramBadRequest as e:
                        logger.error(f"Failed to sync track {track.id}: {e}")
                        stats["failed"] += 1
                        sent_count += 1
                        continue
                
                await session.commit()
                logger.info(f"Sync completed for user {user_id}: {stats}")
                return stats
            finally:
                # Always clear sync status when done
                self._clear_sync_status(user_id)
    
    async def verify_channel_access(
        self,
        channel_id: int,
        bot: Optional[Bot] = None,
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Verify bot has access to send messages to channel.
        
        Returns:
            (success, channel_title, error_message)
        """
        use_bot = bot or self.bot
        if not use_bot:
            return False, None, "Bot not initialized"
        
        try:
            chat = await use_bot.get_chat(channel_id)
            
            # Check if bot can post
            member = await use_bot.get_chat_member(channel_id, use_bot.id)
            
            if member.status not in ("administrator", "creator"):
                return False, chat.title, "Бот должен быть администратором канала"
            
            return True, chat.title, None
            
        except TelegramForbiddenError:
            return False, None, "Бот не имеет доступа к каналу"
        except TelegramBadRequest as e:
            return False, None, f"Ошибка: {e}"


# Global singleton instance
channel_service: ChannelService = ChannelService()


def init_channel_service(bot: Bot) -> ChannelService:
    """Initialize channel service with bot instance"""
    global channel_service
    channel_service.set_bot(bot)
    logger.info("Channel service initialized with bot")
    return channel_service


def get_channel_service() -> ChannelService:
    """Get channel service instance"""
    return channel_service
