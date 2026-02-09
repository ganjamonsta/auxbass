"""
TG Player Bot - Channel Pin Handlers

Handles pinned_message events in user channels.
When a user pins a track message in their channel, the track is marked as liked.
"""
import logging

from aiogram import Router, F
from aiogram.types import Message

from bot.services.channels import get_channel_service

router = Router()
logger = logging.getLogger(__name__)


@router.channel_post(F.pinned_message)
async def handle_channel_pin(message: Message):
    """
    Handle message pin events in channels.
    
    When a message is pinned in a tracked channel, find the corresponding
    track and mark it as liked in the user's library.
    """
    pinned = message.pinned_message
    if not pinned:
        return
    
    channel_id = message.chat.id  # Telegram channel ID (negative)
    pinned_message_id = pinned.message_id
    
    channel_service = get_channel_service()
    
    # Look up the track by channel message
    result = await channel_service.find_track_by_channel_message(
        telegram_channel_id=channel_id,
        message_id=pinned_message_id,
    )
    
    if not result:
        # Not a tracked track message, ignore
        return
    
    user_id, track_id = result
    
    # Mark the track as liked
    liked = await channel_service.like_track_from_pin(user_id, track_id)
    if liked:
        logger.info(f"Track {track_id} liked via channel pin by user {user_id}")
