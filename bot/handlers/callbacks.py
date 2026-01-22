"""
TG Player Bot - Callback Query Handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Track


router = Router()


@router.callback_query(F.data.startswith("delete_track:"))
async def handle_delete_track(callback: CallbackQuery):
    """Handle track deletion"""
    track_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        # Find track
        track = await session.scalar(
            select(Track).where(
                Track.id == track_id,
                Track.user_id == user_id
            )
        )
        
        if not track:
            await callback.answer("Трек не найден", show_alert=True)
            return
        
        track_title = track.title or "Без названия"
        await session.delete(track)
    
    await callback.message.edit_text(
        f"🗑 Трек <b>{track_title}</b> удалён из библиотеки."
    )
    await callback.answer("Удалено!")
