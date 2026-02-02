"""
Скрипт для автоматической загрузки файлов в Telegram Бот (или любой чат).
Работает через MTProto (Pyrogram), что гораздо быстрее и стабильнее, чем Drag-n-Drop.

ТРЕБОВАНИЯ:
pip install pyrogram tgcrypto
"""
import asyncio
import os
from pathlib import Path
from pyrogram import Client
from pyrogram.types import InputMediaAudio

# ================= НАСТРОЙКИ =================
# Папка, где лежат папки batch_xxx (созданные прошлым скриптом)
SOURCE_ROOT = r"f:\Media\auxbass\VK\all\Активный Нормис\organized_for_upload"

# Юзернейм бота или чата, туда будем кидать файлы
TARGET_CHAT = "@tg_player_bot"  # ⚠️ ЗАМЕНИ НА ЮЗЕРНЕЙМ СВОЕГО БОТА

# Ваши API данные (получить на https://my.telegram.org/apps)
# Если нет своих, можно попробовать использовать тестовые, но лучше получить свои.
API_ID = 123456        # ⚠️ ЗАМЕНИ НА СВОЙ API_ID
API_HASH = "changeme"  # ⚠️ ЗАМЕНИ НА СВОЙ API_HASH

# Подпись к каждому файлу (опционально)
CAPTION = "#upload"

# Задержка между файлами (сек), чтобы не словить FloodWait
DELAY = 2 
# =============================================

async def main():
    if API_ID == 123456 or API_HASH == "changeme":
        print("❌ ОШИБКА: Вы не указали API_ID и API_HASH в скрипте!")
        print("1. Зайдите на https://my.telegram.org")
        print("2. Перейдите в API Development tools")
        print("3. Вставьте полученные данные в начало этого скрипта")
        return

    work_dir = Path(SOURCE_ROOT)
    if not work_dir.exists():
        print(f"❌ Папка не найдена: {work_dir}")
        return

    print("🚀 Запуск клиента...")
    # При первом запуске скрипт попросит ввести номер телефона и код из Telegram
    async with Client("my_uploader_session", api_id=API_ID, api_hash=API_HASH) as app:
        
        # Получаем информацию о чате назначения
        try:
            chat = await app.get_chat(TARGET_CHAT)
            print(f"✅ Цель найдена: {chat.title} ({chat.id})")
        except Exception as e:
            print(f"❌ Не удалось найти чат {TARGET_CHAT}: {e}")
            return

        # Ищем все batch папки
        batch_folders = sorted(list(work_dir.glob("batch_*")))
        print(f"📂 Найдено папок для загрузки: {len(batch_folders)}")

        total_files_sent = 0
        
        for folder in batch_folders:
            print(f"\n📂 Обработка папки: {folder.name}")
            
            mp3_files = sorted(list(folder.glob("*.mp3")))
            count = len(mp3_files)
            
            print(f"   Файлов: {count}")
            
            for i, file_path in enumerate(mp3_files, 1):
                try:
                    print(f"   📤 [{i}/{count}] Загрузка: {file_path.name}...")
                    
                    # Отправляем прогресс (можно убрать progress=...)
                    await app.send_audio(
                        chat_id=chat.id,
                        audio=str(file_path),
                        caption=CAPTION,
                        title=file_path.stem  # Имя файла без расширения как название трека
                        # performer="Artist" # Можно пытаться вытащить метаданные, но это медленнее
                    )
                    
                    total_files_sent += 1
                    await asyncio.sleep(DELAY) # Небольшая пауза
                    
                except Exception as e:
                    print(f"   ❌ Ошибка при отправке {file_path.name}: {e}")
                    await asyncio.sleep(5) # Пауза подольше при ошибке

        print(f"\n✅ ГОТОВО! Отправлено файлов: {total_files_sent}")

if __name__ == "__main__":
    try:
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
