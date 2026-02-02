"""
TG Player Bot - Callback Query Handlers v2

Uses new modular service architecture.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack

from bot.services import track_service, album_service, channel_service
from bot.services.session import session_manager
from bot.handlers.keyboards import (
    get_webapp_keyboard,
    get_help_menu_keyboard,
    get_help_back_keyboard,
    get_help_player_keyboard,
)


router = Router()
settings = get_settings()


# ========== Help Section Callbacks ==========

@router.callback_query(F.data == "help:menu")
async def handle_help_menu(callback: CallbackQuery):
    """Return to main help menu"""
    await callback.message.edit_text(
        "🎵 <b>TG Player — Центр помощи</b>\n\n"
        "Добро пожаловать в твою персональную музыкальную библиотеку!\n\n"
        "<b>🚀 Быстрый старт:</b>\n"
        "Просто отправь аудиофайл — всё остальное бот сделает сам.\n\n"
        "Выбери раздел, чтобы узнать больше:",
        reply_markup=get_help_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help:upload")
async def handle_help_upload(callback: CallbackQuery):
    """Show help about uploading music"""
    await callback.message.edit_text(
        "📤 <b>Добавление музыки</b>\n\n"
        "<b>Как добавить треки?</b>\n"
        "Просто отправь аудиофайл боту — готово! "
        "Поддерживаются MP3, FLAC, M4A, OGG и другие форматы.\n\n"
        "<b>✨ Автоматическое обогащение</b>\n"
        "Бот сам найдёт информацию о треке:\n"
        "• Исполнитель, название, альбом\n"
        "• Обложка альбома\n"
        "• Год выпуска и жанр\n"
        "• Номер трека в альбоме\n\n"
        "<b>🔍 Источники данных</b>\n"
        "Метаданные подтягиваются из Deezer и Last.fm "
        "для максимальной точности.\n\n"
        "<b>💾 Вечное хранение</b>\n"
        "Вся музыка хранится прямо в Telegram — "
        "твоя коллекция сохранится навсегда и доступна с любого устройства!",
        reply_markup=get_help_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help:playlists")
async def handle_help_playlists(callback: CallbackQuery):
    """Show help about playlists"""
    await callback.message.edit_text(
        "📁 <b>Плейлисты</b>\n\n"
        "<b>Создание плейлиста:</b>\n"
        "• /playlist — запустить создание\n"
        '• /playlist "Название" — быстрое создание\n\n'
        "<b>Добавление треков:</b>\n"
        "После создания плейлиста просто пересылай "
        "или отправляй аудиофайлы — они автоматически добавятся.\n\n"
        "<b>Управление:</b>\n"
        "• /playlists — список всех плейлистов\n"
        "• Редактирование и удаление через веб-плеер\n\n"
        "<b>✨ Умные функции:</b>\n"
        "• Автоматическое определение дубликатов\n"
        "• Генерация обложки плейлиста\n"
        "• Воспроизведение прямо в Telegram",
        reply_markup=get_help_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help:albums")
async def handle_help_albums(callback: CallbackQuery):
    """Show help about albums and artists"""
    await callback.message.edit_text(
        "💿 <b>Альбомы и исполнители</b>\n\n"
        "<b>Автоматическая организация</b>\n"
        "Бот сам группирует треки по альбомам и исполнителям. "
        "Просто добавляй музыку — структура создастся автоматически.\n\n"
        "<b>🎨 Обложки альбомов</b>\n"
        "Обложки загружаются автоматически из Deezer. "
        "Твоя библиотека выглядит как настоящий музыкальный сервис!\n\n"
        "<b>📊 Полная информация:</b>\n"
        "• Год выпуска альбома\n"
        "• Правильный порядок треков\n"
        "• Группировка по исполнителям\n"
        "• Жанры и теги\n\n"
        "<b>🔍 Удобный поиск</b>\n"
        "Ищи по исполнителю, альбому или названию трека в веб-плеере.",
        reply_markup=get_help_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help:backup")
async def handle_help_backup(callback: CallbackQuery):
    """Show help about cloud backup"""
    await callback.message.edit_text(
        "☁️ <b>Облачный бекап</b>\n\n"
        "<b>Что это?</b>\n"
        "Все треки автоматически дублируются в твой личный канал. "
        "Это надёжный бекап прямо в Telegram!\n\n"
        "<b>🔧 Настройка:</b>\n"
        "1. Создай приватный канал\n"
        "2. Добавь бота администратором\n"
        "3. Команда /channel — привязать канал\n"
        "4. /sync — синхронизировать библиотеку\n\n"
        "<b>✨ Преимущества:</b>\n"
        "• Автоматические хэштеги (#Исполнитель, #Альбом)\n"
        "• Поиск прямо в Telegram\n"
        "• Музыка доступна даже без бота\n"
        "• Можно поделиться с друзьями\n\n"
        "<b>💎 Вечное хранение</b>\n"
        "Telegram не удаляет файлы — твоя музыка сохранится навсегда!",
        reply_markup=get_help_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help:player")
async def handle_help_player(callback: CallbackQuery):
    """Show help about web player"""
    await callback.message.edit_text(
        "🎧 <b>Веб-плеер</b>\n\n"
        "<b>Полноценный музыкальный плеер:</b>\n"
        "• Воспроизведение прямо в Telegram\n"
        "• Работает в браузере на любом устройстве\n"
        "• Красивый современный интерфейс\n\n"
        "<b>🎛 Функции плеера:</b>\n"
        "• Поиск по всей библиотеке\n"
        "• Фильтрация по исполнителям и альбомам\n"
        "• Очередь воспроизведения\n"
        "• Shuffle и Repeat режимы\n"
        "• Редактирование метаданных треков\n\n"
        "<b>🌐 Сайт плеера:</b>\n"
        "<a href=\"https://aux.ganjacraft.ru\">aux.ganjacraft.ru</a>\n\n"
        "<b>🔑 Доступ из браузера:</b>\n"
        "Команда /login — получить код для входа с компьютера. "
        "Слушай музыку на большом экране!\n\n"
        "<b>📱 Mini App</b>\n"
        "Нажми кнопку ниже, чтобы открыть плеер прямо в Telegram.",
        reply_markup=get_help_player_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help:commands")
async def handle_help_commands(callback: CallbackQuery):
    """Show all available commands"""
    await callback.message.edit_text(
        "📱 <b>Все команды</b>\n\n"
        "<b>🎵 Основные:</b>\n"
        "/start — Начать работу с ботом\n"
        "/help — Центр помощи\n"
        "/library — Открыть веб-плеер\n"
        "/stats — Статистика библиотеки\n\n"
        "<b>📁 Плейлисты:</b>\n"
        "/playlist — Создать новый плейлист\n"
        "/playlists — Мои плейлисты\n\n"
        "<b>☁️ Бекап:</b>\n"
        "/channel — Настроить канал\n"
        "/sync — Синхронизировать с каналом\n\n"
        "<a href=\"https://aux.ganjacraft.ru\">aux.ganjacraft.ru</a>\n\n"
        "<b>🌐 Доступ из браузера:</b>\n"
        "Команда /login — получить код для входа с компьютера. "
        "Слушай музыку на большом экране!\n\n"
        "<b>💡 Подсказка:</b>\n"
        "Большинство действий удобнее делать через веб-плеер!",
        reply_markup=get_help_player_keyboard()
    )
    await callback.answer()


# ========== Track Callbacks ==========

@router.callback_query(F.data.startswith("delete_track:"))
async def handle_delete_track(callback: CallbackQuery):
    """Handle track deletion"""
    track_id = int(callback.data.split(":")[1])
    
    track = await track_service.get_track(track_id)
    if not track:
        await callback.answer("Трек не найден", show_alert=True)
        return
    
    track_title = track.title or "Без названия"
    
    success = await track_service.delete_track(track_id)
    if success:
        await callback.message.edit_text(
            f"🗑 Трек <b>{track_title}</b> удалён из библиотеки."
        )
        await callback.answer("Удалено!")
    else:
        await callback.answer("Ошибка удаления", show_alert=True)


@router.callback_query(F.data.startswith("enrich_track:"))
async def handle_enrich_track(callback: CallbackQuery):
    """Handle manual track enrichment"""
    track_id = int(callback.data.split(":")[1])
    
    await callback.answer("Обновление метаданных...")
    
    success = await track_service.trigger_enrichment(track_id)
    
    if success:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply("✅ Метаданные обновлены!")
    else:
        await callback.answer("Не удалось обновить метаданные", show_alert=True)


# ========== Stats Callbacks ==========

@router.callback_query(F.data == "stats:refresh")
async def handle_stats_refresh(callback: CallbackQuery):
    """Refresh stats"""
    user_id = callback.from_user.id
    
    stats = await track_service.get_library_stats(user_id)
    
    total_seconds = stats.get("total_duration_seconds", 0)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    enrichment = stats.get("enrichment", {})
    pending = enrichment.get("pending", 0)
    failed = enrichment.get("failed", 0)
    
    enrichment_text = ""
    if pending > 0:
        enrichment_text = f"\n🔄 Обогащение: {pending} в очереди"
    elif failed > 0:
        enrichment_text = f"\n⚠️ Не обогащено: {failed} треков"
    
    from bot.handlers.keyboards import get_stats_keyboard
    
    await callback.message.edit_text(
        "📊 <b>Статистика библиотеки</b>\n\n"
        f"🎵 Треков: <b>{stats['total_tracks']}</b>\n"
        f"💿 Альбомов: <b>{stats['album_count']}</b>\n"
        f"⏱ Общая длительность: <b>{hours}ч {minutes}мин</b>{enrichment_text}",
        reply_markup=get_stats_keyboard()
    )
    await callback.answer("Обновлено!")


# ========== Channel Callbacks ==========

@router.callback_query(F.data == "channel:verify")
async def handle_channel_verify(callback: CallbackQuery):
    """Verify channel setup"""
    await callback.answer("Перешлите сообщение из вашего канала", show_alert=True)


@router.callback_query(F.data == "channel:help")
async def handle_channel_help(callback: CallbackQuery):
    """Show channel setup help"""
    await callback.message.edit_text(
        "❓ <b>Помощь по настройке канала</b>\n\n"
        "<b>Зачем нужен канал?</b>\n"
        "Ваш личный канал станет бекапом вашей музыки. "
        "Все треки будут пересылаться туда с хэштегами.\n\n"
        "<b>Как настроить:</b>\n"
        "1. Создайте новый приватный канал\n"
        "2. Зайдите в настройки канала → Администраторы\n"
        "3. Добавьте бота и дайте права на публикацию\n"
        "4. Перешлите любое сообщение из канала боту\n\n"
        "<b>Что получите:</b>\n"
        "• Автоматический бекап всех треков\n"
        "• Хэштеги для поиска (#Исполнитель, #Альбом)\n"
        "• Независимое хранилище вашей музыки",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="channel:back"
            )]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "channel:back")
async def handle_channel_back(callback: CallbackQuery):
    """Go back to channel setup"""
    from bot.handlers.keyboards import get_channel_setup_keyboard
    
    await callback.message.edit_text(
        "☁️ <b>Настройка канала для бекапа</b>\n\n"
        "Создайте приватный канал в Telegram и добавьте меня администратором.\n\n"
        "<b>Инструкция:</b>\n"
        "1. Создайте новый канал (приватный)\n"
        "2. Добавьте бота как администратора\n"
        "3. Дайте права на публикацию сообщений\n"
        "4. Перешлите мне любое сообщение из канала",
        reply_markup=get_channel_setup_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "channel:cancel")
async def handle_channel_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel channel setup"""
    await state.clear()
    await callback.message.edit_text("❌ Настройка канала отменена.")
    await callback.answer()


@router.callback_query(F.data == "channel:settings")
async def handle_channel_settings(callback: CallbackQuery):
    """Show channel settings"""
    user_id = callback.from_user.id
    channel = await channel_service.get_user_channel(user_id)
    
    if not channel:
        await callback.answer("Канал не найден", show_alert=True)
        return
    
    # Check if sync is running
    if channel_service.is_sync_active(user_id):
        sync_status = channel_service.get_sync_status(user_id)
        await callback.message.edit_text(
            f"🔄 <b>Синхронизация в процессе...</b>\n\n"
            f"📢 {channel.channel_title or 'Канал'}\n"
            f"⏳ Отправлено: {sync_status['synced']}/{sync_status['total']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⛔ Прервать синхронизацию",
                    callback_data="channel:sync_cancel"
                )],
                [InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="channel:settings"
                )]
            ])
        )
        await callback.answer()
        return
    
    msg_count = await channel_service.get_channel_message_count(user_id)
    
    await callback.message.edit_text(
        f"⚙️ <b>Настройки канала</b>\n\n"
        f"📢 {channel.channel_title or 'Канал'}\n"
        f"🎵 Сохранено: {msg_count} треков\n\n"
        "<b>Опции:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Синхронизировать всё",
                callback_data="channel:sync"
            )],
            [InlineKeyboardButton(
                text="🔍 Найти дубликаты",
                callback_data="channel:duplicates"
            )],
            [InlineKeyboardButton(
                text="❌ Отключить канал",
                callback_data="channel:disconnect_confirm"
            )],
            [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="channel:main"
            )]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "channel:main")
async def handle_channel_main(callback: CallbackQuery):
    """Show main channel status"""
    user_id = callback.from_user.id
    channel = await channel_service.get_user_channel(user_id)
    
    if not channel:
        # No channel - show setup
        from bot.handlers.keyboards import get_channel_setup_keyboard
        await callback.message.edit_text(
            "☁️ <b>Настройка канала для бекапа</b>\n\n"
            "Создайте приватный канал в Telegram и добавьте меня администратором.\n\n"
            "<b>Инструкция:</b>\n"
            "1. Создайте новый канал (приватный)\n"
            "2. Добавьте бота как администратора\n"
            "3. Дайте права на публикацию сообщений\n"
            "4. Перешлите мне любое сообщение из канала",
            reply_markup=get_channel_setup_keyboard()
        )
    else:
        # Has channel - show status
        msg_count = await channel_service.get_channel_message_count(user_id)
        await callback.message.edit_text(
            f"☁️ <b>Бекап в канал</b>\n\n"
            f"📢 {channel.channel_title or 'Канал'}\n"
            f"🎵 Сохранено: <b>{msg_count}</b> треков\n"
            f"#️⃣ Хэштеги: {'✅' if channel.include_hashtags else '❌'}\n\n"
            "Все новые треки автоматически отправляются в канал.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="channel:settings"
                )],
            ])
        )
    await callback.answer()


@router.callback_query(F.data == "channel:sync")
async def handle_channel_sync(callback: CallbackQuery):
    """Start sync from inline button"""
    user_id = callback.from_user.id
    
    # Check if sync is already running
    if channel_service.is_sync_active(user_id):
        sync_status = channel_service.get_sync_status(user_id)
        await callback.answer("Синхронизация уже идёт!", show_alert=True)
        return
    
    channel = await channel_service.get_user_channel(user_id)
    if not channel:
        await callback.answer("Канал не найден", show_alert=True)
        return
    
    # Get sync stats first
    stats = await channel_service.get_sync_stats(user_id)
    
    if stats.get("error"):
        await callback.answer(stats["error"], show_alert=True)
        return
    
    if stats["to_sync"] == 0:
        await callback.message.edit_text(
            f"✅ <b>Все треки уже синхронизированы!</b>\n\n"
            f"📢 {stats['channel_title']}\n"
            f"🎵 В канале: <b>{stats['already_synced']}</b> треков\n"
            f"📚 В библиотеке: <b>{stats['total_tracks']}</b> треков",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="channel:settings")]
            ])
        )
        await callback.answer()
        return
    
    # Show sync started with detailed stats
    await callback.message.edit_text(
        f"🔄 <b>Синхронизация...</b>\n\n"
        f"📢 {stats['channel_title']}\n"
        f"📤 К отправке: <b>{stats['to_sync']}</b> треков\n\n"
        f"⏳ Отправлено: 0/{stats['to_sync']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="⛔ Прервать",
                callback_data="channel:sync_cancel"
            )]
        ])
    )
    await callback.answer()
    
    # Progress callback - update on EVERY track sent
    channel_title = stats['channel_title']
    to_sync_total = stats['to_sync']
    
    async def progress_callback(current, total, synced):
        try:
            await callback.message.edit_text(
                f"🔄 <b>Синхронизация...</b>\n\n"
                f"📢 {channel_title}\n"
                f"📤 К отправке: <b>{total}</b> треков\n\n"
                f"⏳ Отправлено: {synced}/{total}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="⛔ Прервать",
                        callback_data="channel:sync_cancel"
                    )]
                ])
            )
        except:
            pass
    
    result = await channel_service.sync_all_tracks(
        user_id=user_id,
        bot=callback.bot,
        progress_callback=progress_callback
    )
    
    if result.get("error"):
        await callback.message.edit_text(
            f"❌ Ошибка синхронизации: {result['error']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="channel:settings")]
            ])
        )
        return
    
    if result.get("cancelled"):
        await callback.message.edit_text(
            f"⛔ <b>Синхронизация прервана</b>\n\n"
            f"📤 Успешно отправлено: <b>{result['synced']}</b>\n"
            f"⏭️ Уже было в канале: <b>{result['skipped']}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="channel:settings")]
            ])
        )
        return
    
    await callback.message.edit_text(
        f"✅ <b>Синхронизация завершена!</b>\n\n"
        f"📤 Добавлено в канал: <b>{result['synced']}</b>\n"
        f"⏭️ Уже было в канале: <b>{result['skipped']}</b>\n"
        f"❌ Ошибок: <b>{result['failed']}</b>\n"
        f"📊 Всего треков: <b>{result['total']}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="channel:settings")]
        ])
    )


@router.callback_query(F.data == "channel:sync_cancel")
async def handle_channel_sync_cancel(callback: CallbackQuery):
    """Cancel ongoing sync"""
    user_id = callback.from_user.id
    channel_service.request_cancel_sync(user_id)
    await callback.answer("⛔ Прерывание синхронизации...", show_alert=True)


@router.callback_query(F.data == "channel:duplicates")
async def handle_channel_duplicates(callback: CallbackQuery, state: FSMContext):
    """Start deduplication from channel settings"""
    from bot.handlers.deduplication import start_dedup_flow
    await callback.answer()
    await start_dedup_flow(callback, state, callback.from_user.id)


@router.callback_query(F.data == "channel:disconnect_confirm")
async def handle_channel_disconnect_confirm(callback: CallbackQuery):
    """Show disconnect confirmation"""
    await callback.message.edit_text(
        "⚠️ <b>Отключить канал?</b>\n\n"
        "Треки останутся в канале, но новые не будут отправляться.\n"
        "Записи о синхронизированных треках будут удалены.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Да, отключить",
                callback_data="channel:disconnect"
            )],
            [InlineKeyboardButton(
                text="◀️ Отмена",
                callback_data="channel:settings"
            )]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "channel:disconnect")
async def handle_channel_disconnect(callback: CallbackQuery):
    """Disconnect channel"""
    user_id = callback.from_user.id
    
    await channel_service.disable_channel(user_id)
    
    await callback.message.edit_text(
        "✅ Канал отключён.\n\n"
        "Используйте /channel для подключения нового канала."
    )
    await callback.answer("Канал отключён")


# ========== Playlist Creation Callbacks ==========

@router.callback_query(F.data == "playlist:finish")
async def handle_playlist_finish(callback: CallbackQuery):
    """Finish playlist creation and save"""
    user_id = callback.from_user.id
    
    playlist_session = session_manager.get_playlist_session(user_id)
    if not playlist_session:
        await callback.answer("Нет активного плейлиста", show_alert=True)
        return
    
    if playlist_session.track_count == 0:
        await callback.answer("Добавь хотя бы один трек!", show_alert=True)
        return
    
    async with get_session() as session:
        playlist = Playlist(
            user_id=user_id,
            name=playlist_session.name,
            is_public=True,  # Default to public
        )
        session.add(playlist)
        await session.flush()
        
        for position, track_id in enumerate(playlist_session.track_ids):
            pt = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track_id,
                position=position,
            )
            session.add(pt)
        
        playlist_id = playlist.id
    
    session_manager.end_playlist_session(user_id)
    
    await callback.message.edit_text(
        f"🎉 <b>Плейлист создан!</b>\n\n"
        f"📁 «{playlist_session.name}»\n"
        f"🎵 {playlist_session.track_count} треков\n\n"
        f"Открой плеер, чтобы послушать!",
        reply_markup=get_webapp_keyboard()
    )
    await callback.answer("Плейлист создан!")


@router.callback_query(F.data == "playlist:cancel")
async def handle_playlist_cancel(callback: CallbackQuery):
    """Cancel playlist creation"""
    user_id = callback.from_user.id
    
    playlist_session = session_manager.get_playlist_session(user_id)
    if playlist_session:
        session_manager.end_playlist_session(user_id)
        await callback.message.edit_text(
            f"❌ Создание плейлиста «{playlist_session.name}» отменено.\n\n"
            f"Треки остались в библиотеке."
        )
    else:
        await callback.message.edit_text("❌ Отменено.")
    
    await callback.answer()


@router.callback_query(F.data == "playlist:cancel_input")
async def handle_playlist_cancel_input(callback: CallbackQuery, state: FSMContext):
    """Cancel playlist name input"""
    await state.clear()
    await callback.message.edit_text("❌ Создание плейлиста отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith("playlist:add_existing:"))
async def handle_add_existing_to_playlist(callback: CallbackQuery):
    """Add existing track to playlist being created"""
    user_id = callback.from_user.id
    track_id = int(callback.data.split(":")[2])
    
    playlist_session = session_manager.get_playlist_session(user_id)
    if not playlist_session:
        await callback.answer("Нет активного плейлиста", show_alert=True)
        return
    
    if track_id in playlist_session.track_ids:
        await callback.answer("Трек уже в плейлисте!", show_alert=True)
        return
    
    playlist_session.add_track(track_id)
    
    await callback.message.edit_text(
        f"✅ Трек добавлен в плейлист «{playlist_session.name}»!\n\n"
        f"📊 Всего: <b>{playlist_session.track_count}</b> треков",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✓ Завершить ({playlist_session.track_count} треков)",
                    callback_data="playlist:finish"
                ),
                InlineKeyboardButton(
                    text="✗ Отменить",
                    callback_data="playlist:cancel"
                )
            ]
        ])
    )
    await callback.answer("Добавлено!")


@router.callback_query(F.data == "playlist:skip_duplicate")
async def handle_skip_duplicate(callback: CallbackQuery):
    """Skip duplicate track"""
    user_id = callback.from_user.id
    
    playlist_session = session_manager.get_playlist_session(user_id)
    if playlist_session:
        await callback.message.edit_text(
            f"⏭ Трек пропущен.\n\n"
            f"Продолжай отправлять аудио для плейлиста «{playlist_session.name}»\n"
            f"📊 Сейчас: <b>{playlist_session.track_count}</b> треков",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✓ Завершить ({playlist_session.track_count} треков)",
                        callback_data="playlist:finish"
                    ),
                    InlineKeyboardButton(
                        text="✗ Отменить",
                        callback_data="playlist:cancel"
                    )
                ]
            ])
        )
    else:
        await callback.message.edit_text("⏭ Пропущено.")
    
    await callback.answer()


# ========== Playlist Management Callbacks ==========

@router.callback_query(F.data.startswith("pl:menu:"))
async def handle_playlist_menu(callback: CallbackQuery):
    """Show playlist management menu"""
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        playlist = await session.get(
            Playlist, playlist_id,
            options=[selectinload(Playlist.track_associations)]
        )
        
        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        
        track_count = len(playlist.track_associations) if playlist.track_associations else 0
        playlist_name = playlist.name
        created_at = playlist.created_at.strftime('%d.%m.%Y')
    
    await callback.message.edit_text(
        f"📁 <b>{playlist_name}</b>\n\n"
        f"🎵 Треков: {track_count}\n"
        f"📅 Создан: {created_at}\n\n"
        "Выбери действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🎵 Открыть плеер",
                web_app=WebAppInfo(url=f"{settings.webapp_url}?playlist={playlist_id}")
            )],
            [InlineKeyboardButton(
                text="📥 Скачать все треки",
                callback_data=f"download_playlist:{playlist_id}"
            )],
            [
                InlineKeyboardButton(
                    text="✏️ Переименовать",
                    callback_data=f"pl:rename:{playlist_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"pl:delete_confirm:{playlist_id}"
                )
            ],
            [InlineKeyboardButton(
                text="◀️ Назад к списку",
                callback_data="pl:back_to_list"
            )]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pl:rename:"))
async def handle_playlist_rename_start(callback: CallbackQuery, state: FSMContext):
    """Start playlist rename process"""
    from bot.handlers.commands_v2 import PlaylistStates
    
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        
        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        
        playlist_name = playlist.name
    
    await state.set_state(PlaylistStates.waiting_for_rename)
    await state.update_data(rename_playlist_id=playlist_id)
    
    await callback.message.edit_text(
        f"✏️ <b>Переименование плейлиста</b>\n\n"
        f"Текущее название: «{playlist_name}»\n\n"
        "Введи новое название:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✗ Отмена",
                callback_data=f"pl:menu:{playlist_id}"
            )]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pl:delete_confirm:"))
async def handle_playlist_delete_confirm(callback: CallbackQuery):
    """Show delete confirmation"""
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        playlist = await session.get(
            Playlist, playlist_id,
            options=[selectinload(Playlist.track_associations)]
        )
        
        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        
        track_count = len(playlist.track_associations) if playlist.track_associations else 0
        playlist_name = playlist.name
    
    await callback.message.edit_text(
        f"🗑 <b>Удалить плейлист?</b>\n\n"
        f"📁 «{playlist_name}»\n"
        f"🎵 {track_count} треков\n\n"
        "⚠️ Треки останутся в библиотеке.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Да, удалить",
                    callback_data=f"pl:delete:{playlist_id}"
                ),
                InlineKeyboardButton(
                    text="✗ Отмена",
                    callback_data=f"pl:menu:{playlist_id}"
                )
            ]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pl:delete:"))
async def handle_playlist_delete(callback: CallbackQuery):
    """Delete playlist"""
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        
        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        
        playlist_name = playlist.name
        await session.delete(playlist)
    
    await callback.message.edit_text(
        f"✅ Плейлист «{playlist_name}» удалён.\n\n"
        "Треки остались в библиотеке.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="◀️ К плейлистам",
                callback_data="pl:back_to_list"
            )]
        ])
    )
    await callback.answer("Удалено!")


@router.callback_query(F.data == "pl:back_to_list")
async def handle_back_to_playlist_list(callback: CallbackQuery):
    """Return to playlist list"""
    user_id = callback.from_user.id
    
    async with get_session() as session:
        result = await session.execute(
            select(Playlist)
            .options(selectinload(Playlist.track_associations))
            .where(Playlist.user_id == user_id)
            .order_by(Playlist.created_at.desc())
        )
        playlists = result.scalars().all()
        
        playlist_data = []
        for pl in playlists[:20]:
            track_count = len(pl.track_associations) if pl.track_associations else 0
            playlist_data.append({
                'id': pl.id,
                'name': pl.name,
                'track_count': track_count
            })
    
    if not playlist_data:
        await callback.message.edit_text(
            "📁 <b>Мои плейлисты</b>\n\n"
            "У тебя пока нет плейлистов.\n\n"
            "<b>Как создать?</b>\n"
            "• /playlist — интерактивное создание\n"
            '• /playlist "Название" — быстрое создание'
        )
        await callback.answer()
        return
    
    text = "📁 <b>Мои плейлисты</b>\n\n"
    keyboard = []
    
    for pl in playlist_data:
        text += f"• <b>{pl['name']}</b> — {pl['track_count']} 🎵\n"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"📁 {pl['name']}",
                callback_data=f"pl:menu:{pl['id']}"
            )
        ])
    
    text += "\n<b>Управление:</b> нажми на плейлист"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


# ========== General Callbacks ==========

@router.callback_query(F.data == "cancel")
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    """Handle general cancel"""
    await state.clear()
    await callback.message.edit_text("❌ Отменено.")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Handle no-op (page indicator, etc.)"""
    await callback.answer()
