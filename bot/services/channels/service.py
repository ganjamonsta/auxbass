"""
TG Player - User Channel Service

Handles backup of user's music library to their Telegram channel.
Features:
- Forward tracks to user's channel with rate-limiting queue
- Generate hashtags for easy searching
- Update messages when enrichment completes
"""
from typing import Optional, List
from datetime import datetime
from collections import deque
from dataclasses import dataclass
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


def build_track_caption(track, hashtags=None, *, enrichment_override=None):
    """Build a standard caption for a track in a channel message.
    
    Args:
        track: Track model instance
        hashtags: Optional list of hashtag strings
        enrichment_override: If provided, use this instead of track.enrichment
    
    Returns:
        Caption string or None if no parts
    """
    caption_parts = []
    if hasattr(track, 'has_metadata') and not track.has_metadata:
        caption_parts.append(f"🎵 {track.display_title}")
    else:
        if track.title:
            caption_parts.append(f"🎵 {track.title}")
        if track.artist:
            caption_parts.append(f"👤 {track.artist}")
        enr = enrichment_override if enrichment_override is not None else getattr(track, 'enrichment', None)
        if enr and enr.album_name:
            caption_parts.append(f"💿 {enr.album_name}")
    
    if hashtags:
        caption_parts.append("")
        caption_parts.append(format_hashtags(hashtags))
    
    return "\n".join(caption_parts) if caption_parts else None


@dataclass
class ForwardQueueItem:
    """Item in the forward queue"""
    user_id: int
    track_id: int
    added_at: datetime


class ChannelService:
    """Service for managing user channels and messages"""
    
    # Delay between forwarding tracks (seconds) - Telegram allows ~20 msg/min
    FORWARD_DELAY = 3.0
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self._cancel_sync: dict[int, bool] = {}  # user_id -> cancel flag
        self._active_sync: dict[int, dict] = {}  # user_id -> sync status info
        
        # Forward queue for rate-limited sending
        self._forward_queue: deque[ForwardQueueItem] = deque()
        self._queue_worker_task: Optional[asyncio.Task] = None
        self._queue_running = False
    
    def set_bot(self, bot: Bot):
        """Set bot instance for sending messages"""
        self.bot = bot
    
    async def start_queue_worker(self):
        """Start background queue worker for rate-limited forwarding"""
        if self._queue_running:
            return
        
        self._queue_running = True
        self._queue_worker_task = asyncio.create_task(self._queue_worker_loop())
        logger.info("Channel forward queue worker started")
    
    async def stop_queue_worker(self):
        """Stop background queue worker"""
        self._queue_running = False
        if self._queue_worker_task:
            self._queue_worker_task.cancel()
            try:
                await self._queue_worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Channel forward queue worker stopped")
    
    async def _queue_worker_loop(self):
        """Main loop for processing forward queue with rate limiting"""
        while self._queue_running:
            try:
                if self._forward_queue:
                    item = self._forward_queue.popleft()
                    await self._forward_track_immediately(
                        user_id=item.user_id,
                        track_id=item.track_id,
                    )
                    # Delay to avoid rate limiting
                    await asyncio.sleep(self.FORWARD_DELAY)
                else:
                    # No items in queue, sleep briefly
                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Forward queue worker error: {e}")
                await asyncio.sleep(1)
    
    def queue_track_for_forward(self, user_id: int, track_id: int):
        """
        Add track to forward queue for rate-limited sending.
        Uses the same mechanism as manual sync.
        """
        item = ForwardQueueItem(
            user_id=user_id,
            track_id=track_id,
            added_at=datetime.utcnow(),
        )
        self._forward_queue.append(item)
        logger.debug(f"Track {track_id} queued for forward (queue size: {len(self._forward_queue)})")
    
    def get_queue_size(self, user_id: Optional[int] = None) -> int:
        """Get current queue size, optionally filtered by user"""
        if user_id is None:
            return len(self._forward_queue)
        return sum(1 for item in self._forward_queue if item.user_id == user_id)
    
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
        immediate: bool = False,
    ) -> bool:
        """
        Queue a track for forwarding to user's channel with hashtags.
        Uses rate-limited queue to avoid Telegram flood limits.
        
        Args:
            user_id: User who owns the channel
            track_id: Track ID to forward
            bot: Bot instance for sending (used if immediate=True)
            immediate: If True, send immediately without queue (for sync)
        
        Returns:
            True if queued/forwarded successfully, False otherwise
        """
        if immediate:
            return await self._forward_track_immediately(user_id, track_id, bot)
        
        # Check if channel exists and auto_forward is enabled before queuing
        async with get_session() as session:
            channel = await session.scalar(
                select(UserChannel).where(
                    UserChannel.user_id == user_id,
                    UserChannel.is_active == True
                )
            )
            
            if not channel or not channel.auto_forward:
                return False
            
            # Check if track already sent to channel
            existing = await session.scalar(
                select(ChannelMessage).where(
                    ChannelMessage.channel_id == channel.id,
                    ChannelMessage.track_id == track_id,
                )
            )
            if existing:
                logger.debug(f"Track {track_id} already in channel, skipping queue")
                return True  # Already sent, consider success
        
        # Add to queue for rate-limited sending
        self.queue_track_for_forward(user_id, track_id)
        return True
    
    async def _forward_track_immediately(
        self,
        user_id: int,
        track_id: int,
        bot: Optional[Bot] = None,
    ) -> bool:
        """
        Forward a track to user's channel immediately (internal use).
        Used by queue worker and sync_all_tracks.
        
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
            
            # Check if already sent (avoid duplicates from queue)
            existing = await session.scalar(
                select(ChannelMessage).where(
                    ChannelMessage.channel_id == channel.id,
                    ChannelMessage.track_id == track_id,
                )
            )
            if existing:
                logger.debug(f"Track {track_id} already sent to channel, skipping")
                return True
            
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
                # Generate hashtags (only for tracks with real metadata)
                hashtags = []
                if channel.include_hashtags and track.has_metadata:
                    enrichment = track.enrichment
                    hashtags = generate_hashtags(
                        artist=track.artist,
                        title=track.title,
                        album=enrichment.album_name if enrichment else None,
                        genre=enrichment.genre if enrichment else None,
                        extra_tags=enrichment.tags if enrichment else None,
                    )
                
                caption = build_track_caption(track, hashtags)
                
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
                
            except TelegramRetryAfter as e:
                # Rate limited - wait and retry
                logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after + 1)
                # Re-queue for retry
                self.queue_track_for_forward(user_id, track_id)
                return False
                
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
                    extra_tags=track.enrichment.tags if track.enrichment else None,
                )
                
                caption = build_track_caption(track, new_hashtags)
                
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
    
    async def update_incomplete_messages(
        self,
        user_id: Optional[int] = None,
        bot: Optional[Bot] = None,
        progress_callback=None,
    ) -> dict:
        """
        Update channel messages for tracks that were synced before enrichment completed.
        Finds messages where track now has enrichment data but message has incomplete hashtags.
        
        OPTIMIZED: Pre-calculates expected hashtags and only processes messages that need updates.
        
        Args:
            user_id: Specific user to update, or None for all users
            bot: Bot instance
            progress_callback: Optional async callback(current, total, updated)
        
        Returns:
            Dict with update results: {checked, updated, failed}
        """
        use_bot = bot or self.bot
        if not use_bot:
            logger.error("No bot instance available for updating messages")
            return {"checked": 0, "updated": 0, "failed": 0}
        
        stats = {"checked": 0, "updated": 0, "failed": 0, "skipped": 0}
        
        async with get_session() as session:
            # Build query for ALL channel messages for this user
            # We'll check each message and update if hashtags differ from expected
            # This covers: incomplete enrichment, new enrichment data, featured artists from title
            query = (
                select(ChannelMessage)
                .join(Track, ChannelMessage.track_id == Track.id)
                .join(UserChannel, ChannelMessage.channel_id == UserChannel.id)
                .outerjoin(TrackEnrichment, Track.id == TrackEnrichment.track_id)
                .where(
                    UserChannel.is_active == True,
                    UserChannel.include_hashtags == True,
                )
                .options(
                    selectinload(ChannelMessage.track).selectinload(Track.enrichment),
                    selectinload(ChannelMessage.channel),
                )
            )
            
            if user_id:
                query = query.where(UserChannel.user_id == user_id)
            
            result = await session.execute(query)
            messages = result.scalars().all()
            
            total = len(messages)
            logger.info(f"Checking {total} channel messages for incomplete hashtags")
            
            # OPTIMIZATION: Pre-calculate all expected hashtags in memory first
            # This is much faster than doing it during iteration with API calls
            messages_to_update = []
            
            for msg in messages:
                track = msg.track
                enrichment = track.enrichment
                
                # Parse current hashtags
                current_hashtags = []
                if msg.hashtags:
                    try:
                        current_hashtags = json.loads(msg.hashtags)
                    except:
                        current_hashtags = []
                
                # Generate what hashtags should be (works even without enrichment)
                expected_hashtags = generate_hashtags(
                    artist=track.artist,
                    title=track.title,
                    album=enrichment.album_name if enrichment else None,
                    genre=enrichment.genre if enrichment else None,
                    extra_tags=enrichment.tags if enrichment else None,
                )
                
                # Check if update needed (compare sets to ignore order)
                if set(current_hashtags) == set(expected_hashtags):
                    stats["skipped"] += 1
                    continue  # Already up to date
                
                caption = build_track_caption(track, expected_hashtags, enrichment_override=enrichment)
                
                messages_to_update.append({
                    "msg": msg,
                    "channel": msg.channel,
                    "caption": caption,
                    "expected_hashtags": expected_hashtags,
                })
            
            stats["checked"] = total
            update_total = len(messages_to_update)
            logger.info(f"Found {update_total} messages that need hashtag updates (skipped {stats['skipped']} up-to-date)")
            
            # If nothing to update, return early
            if update_total == 0:
                if progress_callback:
                    try:
                        await progress_callback(total, total, 0)
                    except:
                        pass
                return stats
            
            # OPTIMIZATION: Progress update every 50 messages or 10% of total, whichever is smaller
            progress_step = min(50, max(1, update_total // 10))
            last_progress_update = 0
            batch_count = 0
            
            for i, item in enumerate(messages_to_update):
                msg = item["msg"]
                channel = item["channel"]
                caption = item["caption"]
                expected_hashtags = item["expected_hashtags"]
                
                # Update progress less frequently to reduce Telegram API overhead
                if progress_callback and (i - last_progress_update >= progress_step or i == 0):
                    try:
                        await progress_callback(stats["skipped"] + i, total, stats["updated"])
                        last_progress_update = i
                    except:
                        pass
                
                try:
                    await use_bot.edit_message_caption(
                        chat_id=channel.channel_id,
                        message_id=msg.message_id,
                        caption=caption,
                        parse_mode="HTML",
                    )
                    
                    msg.hashtags = json.dumps(expected_hashtags)
                    msg.updated_at = datetime.utcnow()
                    stats["updated"] += 1
                    batch_count += 1
                    
                    # OPTIMIZATION: Minimal rate limiting - Telegram allows ~30 edits/sec for own channels
                    # Only add delay every 20 messages to stay well under limits
                    if batch_count >= 20:
                        await asyncio.sleep(0.5)
                        batch_count = 0
                    
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        pass  # Same content - no delay needed
                    elif "message to edit not found" in str(e).lower():
                        # Message was deleted, remove record
                        await session.delete(msg)
                    else:
                        logger.error(f"Failed to update message {msg.message_id}: {e}")
                        stats["failed"] += 1
                except TelegramForbiddenError:
                    channel.is_active = False
                    stats["failed"] += 1
                    break  # No point continuing if we lost access
                except TelegramRetryAfter as e:
                    logger.warning(f"Rate limited, waiting {e.retry_after}s")
                    await asyncio.sleep(e.retry_after + 1)
                    batch_count = 0  # Reset batch counter
                    # Don't count as failed, will be caught next time
            
            # Final progress update
            if progress_callback:
                try:
                    await progress_callback(total, total, stats["updated"])
                except:
                    pass
            
            await session.commit()
        
        logger.info(f"Updated incomplete messages: {stats}")
        return stats

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
            
            # Get already synced track IDs and messages
            synced_result = await session.execute(
                select(ChannelMessage).where(
                    ChannelMessage.channel_id == channel.id
                )
            )
            synced_messages = synced_result.scalars().all()
            synced_track_ids = {msg.track_id for msg in synced_messages}
            
            # Find tracks to delete (in channel but not in library anymore)
            library_track_ids = {t.id for t in tracks}
            tracks_to_delete = [msg for msg in synced_messages if msg.track_id not in library_track_ids]
            
            stats = {"synced": 0, "skipped": 0, "failed": 0, "deleted": 0, "total": len(tracks), "cancelled": False}
            
            # Delete tracks that were removed from library
            for msg in tracks_to_delete:
                try:
                    await use_bot.delete_message(
                        chat_id=channel.channel_id,
                        message_id=msg.message_id
                    )
                except (TelegramBadRequest, TelegramForbiddenError) as e:
                    logger.debug(f"Could not delete message {msg.message_id}: {e}")
                
                # Always delete the record (message may have been deleted manually)
                await session.delete(msg)
                stats["deleted"] += 1
            
            if tracks_to_delete:
                await session.commit()
                logger.info(f"Deleted {len(tracks_to_delete)} removed tracks from channel for user {user_id}")
            
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
                                extra_tags=enrichment.tags if enrichment else None,
                            )
                        
                        caption = build_track_caption(track, hashtags)
                        
                        # Send audio
                        sent_message = await use_bot.send_audio(
                            chat_id=channel.channel_id,
                            audio=track.file_id,
                            caption=caption,
                            parse_mode="HTML",
                        )
                        
                        # Save message record IMMEDIATELY to prevent duplicates on restart
                        channel_message = ChannelMessage(
                            channel_id=channel.id,
                            track_id=track.id,
                            message_id=sent_message.message_id,
                            hashtags=json.dumps(hashtags) if hashtags else None,
                        )
                        session.add(channel_message)
                        await session.commit()  # Commit after each track!
                        
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
                        await session.commit()
                        break  # Stop sync if access lost
                        
                    except TelegramBadRequest as e:
                        logger.error(f"Failed to sync track {track.id}: {e}")
                        stats["failed"] += 1
                        sent_count += 1
                        continue
                
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

    async def delete_track_from_channel(
        self,
        user_id: int,
        track_id: int,
        bot: Optional[Bot] = None,
    ) -> bool:
        """
        Delete a track message from user's channel.
        
        Args:
            user_id: User who owns the channel
            track_id: Track ID to delete
            bot: Bot instance for deleting
        
        Returns:
            True if deleted successfully, False otherwise
        """
        use_bot = bot or self.bot
        if not use_bot:
            logger.error("No bot instance available for deleting")
            return False
        
        async with get_session() as session:
            # Get channel
            channel = await session.scalar(
                select(UserChannel).where(
                    UserChannel.user_id == user_id,
                    UserChannel.is_active == True
                )
            )
            
            if not channel:
                return False
            
            # Get channel message record
            result = await session.execute(
                select(ChannelMessage).where(
                    ChannelMessage.channel_id == channel.id,
                    ChannelMessage.track_id == track_id
                )
            )
            channel_message = result.scalar_one_or_none()
            
            if not channel_message:
                # No message to delete
                return False
            
            try:
                # Delete message from Telegram
                await use_bot.delete_message(
                    chat_id=channel.channel_id,
                    message_id=channel_message.message_id
                )
                
                # Delete record from database
                await session.delete(channel_message)
                await session.commit()
                
                logger.info(f"Track {track_id} message deleted from channel {channel.channel_id}")
                return True
                
            except TelegramForbiddenError:
                logger.warning(f"Bot removed from channel {channel.channel_id}")
                return False
                
            except TelegramBadRequest as e:
                # Message might already be deleted
                if "message to delete not found" in str(e).lower():
                    # Still delete the record
                    await session.delete(channel_message)
                    await session.commit()
                    logger.info(f"Track {track_id} message record deleted (message already gone)")
                    return True
                logger.error(f"Failed to delete message from channel: {e}")
                return False


# Global singleton instance
channel_service: ChannelService = ChannelService()


def init_channel_service(bot: Bot) -> ChannelService:
    """Initialize channel service with bot instance"""
    global channel_service
    channel_service.set_bot(bot)
    logger.info("Channel service initialized with bot")
    return channel_service


async def start_channel_service():
    """Start channel service background workers (queue worker)"""
    await channel_service.start_queue_worker()


async def stop_channel_service():
    """Stop channel service background workers"""
    await channel_service.stop_queue_worker()


def get_channel_service() -> ChannelService:
    """Get channel service instance"""
    return channel_service
