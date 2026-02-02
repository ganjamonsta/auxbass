"""
TG Player Bot - Deduplication Handlers

Handlers for analyzing and resolving duplicates.
"""
from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.matching import generate_hashtags, format_hashtags
from shared.models import Track
from bot.services.deduplication import deduplication_service, get_approx_bitrate, is_hd_version
from bot.handlers.keyboards import get_deduplication_action_keyboard

router = Router()

class DedupStates(StatesGroup):
    viewing = State()

@router.message(Command("duplicates"))
async def cmd_duplicates(message: Message, state: FSMContext):
    """Start deduplication analysis (Command)"""
    await start_dedup_flow(message, state, message.from_user.id)

@router.callback_query(F.data == "stats:dedup")
async def callback_duplicates(callback: CallbackQuery, state: FSMContext):
    """Start deduplication analysis (Callback)"""
    await callback.answer()
    await start_dedup_flow(callback, state, callback.from_user.id)

async def start_dedup_flow(event_obj, state: FSMContext, user_id: int):
    """Common entry point"""
    status_msg = None
    if isinstance(event_obj, Message):
        status_msg = await event_obj.answer("🔄 Анализирую медиатеку на наличие дубликатов...")
    elif isinstance(event_obj, CallbackQuery):
        # maybe separate message?
        status_msg = await event_obj.message.answer("🔄 Анализирую медиатеку на наличие дубликатов...")
    
    stats = await deduplication_service.get_duplicate_stats(user_id)
    
    if stats['duplicate_groups_count'] == 0:
        text = "✅ Дубликатов не найдено! Ваша библиотека чиста."
        if status_msg:
            await status_msg.edit_text(text)
        elif isinstance(event_obj, CallbackQuery):
            await event_obj.message.answer(text)
        return

    if status_msg:
        await status_msg.delete()
    
    # Save state
    await state.set_state(DedupStates.viewing)
    await state.update_data(
        total_groups=stats['duplicate_groups_count'],
        current_offset=0
    )
    
    await show_duplicate_group(event_obj if isinstance(event_obj, Message) else event_obj.message, state, 0)


async def show_duplicate_group(message_obj, state: FSMContext, offset: int, confirm_delete_id: Optional[int] = None):
    """Show specific duplicate group"""
    user_id = message_obj.from_user.id
    
    # Get group
    group_data = await deduplication_service.get_next_duplicate_group(user_id, offset)
    if not group_data:
        await message_obj.answer("✅ Проверка завершена!")
        await state.clear()
        return

    group_key, tracks = group_data
    data = await state.get_data()
    total = data.get('total_groups', 0)
    
    # Prepare text
    text = (
        f"🔍 <b>Группа {offset + 1} из {total}</b>\n"
        f"🔑 Ключ: <i>{group_key}</i>\n\n"
    )
    
    for idx, track in enumerate(tracks):
        # Format track info
        meta_parts = []
        if track.duration:
            m, s = divmod(track.duration, 60)
            meta_parts.append(f"{m}:{s:02d}")
        if track.file_size:
            mb = track.file_size / (1024 * 1024)
            meta_parts.append(f"{mb:.1f} MB")
        
        # Add quality info (bitrate)
        bitrate = get_approx_bitrate(track)
        if bitrate:
            meta_parts.append(f"~{int(bitrate)} kbps")
        
        # Hashtags preview
        hashtags = []
        enrichment = track.enrichment
        hashtags = generate_hashtags(
            artist=track.artist,
            title=track.title,
            album=enrichment.album_name if enrichment else None,
            genre=enrichment.genre if enrichment else None,
        )
        tag_str = format_hashtags(hashtags[:5]) # Show first 5 keys
        if len(hashtags) > 5:
            tag_str += "..."
            
        text += (
            f"<b>#{idx + 1}</b>: {track.artist} - {track.title}\n"
            f"├ ⏱ { ' | '.join(meta_parts) }\n"
            f"├ 🏷 {tag_str}\n"
            f"└ 🆔 {track.id}\n\n"
        )

    # Use answer or edit_text depending on context
    keyboard = get_deduplication_action_keyboard(tracks, offset, total, confirm_delete_id)
    
    if isinstance(message_obj, CallbackQuery):
        await message_obj.message.edit_text(text, reply_markup=keyboard)
    else:
        await message_obj.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("dedup:"))
async def handle_dedup_action(callback: CallbackQuery, state: FSMContext):
    """Handle deduplication actions"""
    action = callback.data.split(":")[1]
    data = await state.get_data()
    offset = data.get("current_offset", 0)
    
    if action == "next":
        # Skip this group (keep all tracks)
        await state.update_data(current_offset=offset + 1)
        await show_duplicate_group(callback, state, offset + 1)
    
    elif action == "noop":
        # Do nothing (info button clicked)
        await callback.answer()
        
    elif action == "delete":
        # dedup:delete:TRACK_ID - show confirmation
        delete_id = int(callback.data.split(":")[2])
        await callback.answer("⚠️ Подтвердите удаление")
        # Re-render with confirmation buttons
        await show_duplicate_group(callback, state, offset, confirm_delete_id=delete_id)
        
    elif action == "cancel_delete":
        # Cancel deletion confirmation
        await callback.answer("❌ Отменено")
        await show_duplicate_group(callback, state, offset)
        
    elif action == "confirm_delete":
        # dedup:confirm_delete:TRACK_ID - actually delete
        delete_id = int(callback.data.split(":")[2])
        
        # Delete this specific track
        await deduplication_service.delete_single_track(delete_id, callback.from_user.id)
        await callback.answer("🗑 Трек удалён")
        
        # Check if group still has duplicates after deletion
        await show_duplicate_group(callback, state, offset)
        
    elif action == "play":
        track_id = int(callback.data.split(":")[2])
        # Send audio for preview
        from shared.database import get_session
        async with get_session() as session:
             track = await session.get(Track, track_id)
             if track:
                 await callback.message.reply_audio(track.file_id, caption=f"🎧 Проверка: {track.title}")
        await callback.answer()
        
    elif action == "cancel":
        await state.clear()
        await callback.message.edit_text("✅ Проверка дубликатов завершена.")

