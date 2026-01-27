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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

import sys
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
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def setup_channel(
        self,
        session: AsyncSession,
        user_id: int,
        channel_id: int,
        channel_username: Optional[str] = None,
        channel_title: Optional[str] = None,
    ) -> UserChannel:
        """
        Setup or update user's channel for library backup.
        
        Args:
            user_id: Telegram user ID
            channel_id: Telegram channel ID (negative number)
            channel_username: Channel @username (optional)
            channel_title: Channel title (optional)
        
        Returns:
            UserChannel object
        """
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
        session: AsyncSession,
        user_id: int
    ) -> Optional[UserChannel]:
        """Get user's channel if configured"""
        return await session.scalar(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.is_active == True
            )
        )
    
    async def disable_channel(
        self,
        session: AsyncSession,
        user_id: int
    ) -> bool:
        """Disable user's channel (don't delete, just deactivate)"""
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
        session: AsyncSession,
        user_id: int,
        track: Track,
        original_message: Message,
    ) -> Optional[ChannelMessage]:
        """
        Forward a track to user's channel with hashtags.
        
        Args:
            user_id: User who owns the channel
            track: Track to forward
            original_message: Original message with audio
        
        Returns:
            ChannelMessage record if successful, None otherwise
        """
        channel = await self.get_user_channel(session, user_id)
        
        if not channel or not channel.auto_forward:
            return None
        
        try:
            # Generate hashtags
            hashtags = []
            if channel.include_hashtags:
                hashtags = generate_hashtags(
                    artist=track.artist,
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
            
            caption = "\n".join(caption_parts) if caption_parts else None
            
            # Forward the audio
            sent_message = await self.bot.send_audio(
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
            
            logger.info(f"Track {track.id} forwarded to channel {channel.channel_id}")
            return channel_message
            
        except TelegramForbiddenError:
            # Bot was removed from channel
            logger.warning(f"Bot removed from channel {channel.channel_id}, disabling")
            channel.is_active = False
            return None
            
        except TelegramBadRequest as e:
            logger.error(f"Failed to forward to channel: {e}")
            return None
    
    async def update_channel_message(
        self,
        session: AsyncSession,
        track_id: int,
    ) -> int:
        """
        Update all channel messages for a track (after enrichment).
        Updates hashtags based on new metadata.
        
        Returns:
            Number of messages updated
        """
        # Get track with enrichment
        track = await session.get(Track, track_id)
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
                await self.bot.edit_message_caption(
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
    
    async def verify_channel_access(
        self,
        channel_id: int
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Verify bot has access to send messages to channel.
        
        Returns:
            (success, channel_title, error_message)
        """
        try:
            chat = await self.bot.get_chat(channel_id)
            
            # Check if bot can post
            member = await self.bot.get_chat_member(channel_id, self.bot.id)
            
            if member.status not in ("administrator", "creator"):
                return False, chat.title, "Бот должен быть администратором канала"
            
            return True, chat.title, None
            
        except TelegramForbiddenError:
            return False, None, "Бот не имеет доступа к каналу"
        except TelegramBadRequest as e:
            return False, None, f"Ошибка: {e}"


# Global instance (will be initialized with bot)
channel_service: Optional[ChannelService] = None


def init_channel_service(bot: Bot):
    """Initialize channel service with bot instance"""
    global channel_service
    channel_service = ChannelService(bot)
    return channel_service


def get_channel_service() -> ChannelService:
    """Get channel service instance"""
    if channel_service is None:
        raise RuntimeError("Channel service not initialized. Call init_channel_service first.")
    return channel_service
