"""
TG Player Bot - Channel Member Event Handlers

Handles bot membership changes in channels (my_chat_member updates).
Automatically detects when the bot is promoted to administrator or removed/demoted in user channels,
updating the database and notifying the user.
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import (
    ChatMemberUpdated,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters.chat_member_updated import (
    ChatMemberUpdatedFilter,
    KICKED,
    LEFT,
    RESTRICTED,
    MEMBER,
    ADMINISTRATOR,
    CREATOR,
)
from sqlalchemy import select

from shared.database import get_session
from shared.models import UserChannel, utcnow
from bot.services.channels import get_channel_service

router = Router(name="channel_events")
logger = logging.getLogger(__name__)


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(
            (KICKED | LEFT | RESTRICTED | MEMBER)
            >> (ADMINISTRATOR | CREATOR)
        )
    )
)
async def handle_bot_promoted_to_admin(event: ChatMemberUpdated):
    """
    Handle bot promoted to administrator in a channel.
    If this channel belongs to a known user, re-activate it and restore unavailable tracks.
    If it's newly added, offer to connect it as backup channel.
    """
    if event.chat.type != "channel":
        return

    channel_id = event.chat.id
    channel_title = event.chat.title or "Музыкальный канал"
    channel_username = event.chat.username
    from_user_id = event.from_user.id if event.from_user else None

    logger.info(f"Bot was promoted to administrator in channel '{channel_title}' ({channel_id}) by user {from_user_id}")

    ch_svc = get_channel_service()
    bot_info = await event.bot.get_me()

    async with get_session() as session:
        # Check if this channel is already registered to someone
        existing_channel = await session.scalar(
            select(UserChannel).where(UserChannel.channel_id == channel_id)
        )

        if existing_channel:
            # Re-activate channel if it was deactivated
            was_inactive = not existing_channel.is_active
            existing_channel.is_active = True
            existing_channel.channel_title = channel_title
            existing_channel.channel_username = channel_username
            existing_channel.updated_at = utcnow()
            target_user_id = existing_channel.user_id
            await session.commit()

            # Reconcile tracks that were falsely marked unavailable while bot was absent
            restored_count = await ch_svc.reconcile_channel_tracks(target_user_id)

            # Notify the channel owner
            try:
                restored_msg = f"\n\n♻️ Восстановлен доступ к <b>{restored_count}</b> ранее недоступным трекам." if restored_count > 0 else ""
                await event.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        f"✅ <b>Связь с каналом восстановлена!</b>\n\n"
                        f"📢 <b>{channel_title}</b>\n\n"
                        f"Бот снова имеет права администратора. Резервное копирование и стриминг треков из канала активны.{restored_msg}"
                    ),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎵 Открыть плеер", url=f"https://t.me/{bot_info.username}?startapp=library")],
                        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:channel")],
                    ]),
                )
            except Exception as e:
                logger.debug(f"Failed to send promotion notification to user {target_user_id}: {e}")
            return

        # Channel is not registered yet, but added by a user
        if from_user_id:
            # Check if this user already has another channel
            user_has_channel = await session.scalar(
                select(UserChannel).where(
                    UserChannel.user_id == from_user_id,
                    UserChannel.is_active == True,
                )
            )

            try:
                if not user_has_channel:
                    text = (
                        f"📢 <b>Вы добавили бота администратором в канал «{channel_title}»!</b>\n\n"
                        f"Хотите подключить его как резервный канал для вашей музыки в TG Player?"
                    )
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Подключить этот канал", callback_data=f"ch:connect:{channel_id}")],
                        [InlineKeyboardButton(text="Отмена", callback_data="menu:main")],
                    ])
                else:
                    text = (
                        f"📢 <b>Бот добавлен в канал «{channel_title}».</b>\n\n"
                        f"У вас уже подключён канал «{user_has_channel.channel_title or 'Резервный'}». "
                        f"Хотите переключиться на этот новый канал?"
                    )
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 Сменить канал на этот", callback_data=f"ch:connect:{channel_id}")],
                        [InlineKeyboardButton(text="Оставить прежний", callback_data="menu:channel")],
                    ])

                await event.bot.send_message(
                    chat_id=from_user_id,
                    text=text,
                    reply_markup=kb,
                )
            except Exception as e:
                logger.debug(f"Failed to send channel connection prompt to user {from_user_id}: {e}")


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(
            (ADMINISTRATOR | CREATOR | MEMBER)
            >> (KICKED | LEFT | RESTRICTED)
        )
    )
)
async def handle_bot_demoted_or_kicked(event: ChatMemberUpdated):
    """
    Handle bot removed from channel or permissions revoked.
    Deactivates UserChannel in DB and alerts the user immediately in PM.
    """
    if event.chat.type != "channel":
        return

    channel_id = event.chat.id
    channel_title = event.chat.title or "Музыкальный канал"
    logger.warning(f"Bot was removed or demoted in channel '{channel_title}' ({channel_id})")

    async with get_session() as session:
        channel = await session.scalar(
            select(UserChannel).where(UserChannel.channel_id == channel_id)
        )

        if not channel:
            return

        if channel.is_active:
            channel.is_active = False
            channel.updated_at = utcnow()
            await session.commit()
            logger.info(f"Deactivated channel {channel_id} for user {channel.user_id} due to bot removal")

            bot_info = await event.bot.get_me()
            try:
                await event.bot.send_message(
                    chat_id=channel.user_id,
                    text=(
                        f"⚠️ <b>Внимание: потерян доступ к каналу «{channel_title}»</b>\n\n"
                        f"Бот @{bot_info.username} был удалён из канала или потерял права администратора.\n\n"
                        f"• Резервное копирование новых треков приостановлено.\n"
                        f"• Треки, требующие обновления ссылок из канала, не смогут воспроизводиться.\n\n"
                        f"Чтобы возобновить работу, снова добавьте бота администратором в этот канал "
                        f"или подключите другой канал через /channel."
                    ),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⚙️ Настройки канала", callback_data="menu:channel")]
                    ]),
                )
            except Exception as e:
                logger.debug(f"Failed to send demotion alert to user {channel.user_id}: {e}")
