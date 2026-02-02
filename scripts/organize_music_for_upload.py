"""
Скрипт для организации музыкальных файлов для загрузки в Telegram.
Раскладывает файлы по папкам для удобного drag-and-drop.
"""
import os
import shutil
from pathlib import Path
from typing import List, Tuple
import json
import re


# Настройки
FILES_PER_BATCH = 50  # Сколько файлов в одной папке

# Telegram лимиты:
# - Обычный Bot API: 50 МБ (для ботов)
# - С Telegram Premium: до 4 ГБ (для пользователей, но бот должен использовать Local Bot API)
# - Local Bot API Server: без лимита
TELEGRAM_PREMIUM = True  # У вас есть Premium?
MAX_FILE_SIZE_MB = 2000 if TELEGRAM_PREMIUM else 50  # МБ

SOURCE_DIR = r"f:\Media\auxbass\VK\all\Активный Нормис\zip"
OUTPUT_DIR = r"f:\Media\auxbass\VK\all\Активный Нормис\organized_for_upload"


def get_file_size_mb(file_path: Path) -> float:
    """Получить размер файла в МБ"""
    return file_path.stat().st_size / (1024 * 1024)


def collect_files(source_dir: Path) -> List[Tuple[Path, float]]:
    """
    Собрать все MP3 файлы с информацией о размере
    
    Returns:
        List of (file_path, size_mb) tuples
    """
    files = []
    
    if not source_dir.exists():
        print(f"❌ Папка не найдена: {source_dir}")
        return files
    
    for file_path in source_dir.glob("*.mp3"):
        size_mb = get_file_size_mb(file_path)
        files.append((file_path, size_mb))
    
    # Сортируем по имени (с учетом чисел, чтобы 1, 2, 10, а не 1, 10, 2)
    files.sort(key=lambda x: [
        int(t) if t.isdigit() else t.lower() 
        for t in re.split(r'(\d+)', x[0].name)
    ])
    
    return files


def organize_files(files: List[Tuple[Path, float]], output_dir: Path, files_per_batch: int, max_size_mb: float):
    """
    Организовать файлы по папкам
    """
    # Создаем выходную директорию
    if output_dir.exists():
        print(f"⚠️  Папка {output_dir} уже существует")
        response = input("Удалить и пересоздать? (y/n): ").strip().lower()
        if response == 'y':
            shutil.rmtree(output_dir)
        else:
            print("❌ Отменено")
            return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Статистика
    total_files = len(files)
    oversized_files = []
    copied_files = 0
    current_batch = 1
    batch_file_count = 0
    
    # Создаем папку для текущего батча
    batch_dir = output_dir / f"batch_{current_batch:03d}"
    batch_dir.mkdir(exist_ok=True)
    
    print(f"\n📦 Начинаем организацию файлов...")
    print(f"   Всего файлов: {total_files}")
    print(f"   Файлов в папке: {files_per_batch}")
    print(f"   Макс. размер: {max_size_mb} МБ\n")
    
    for file_path, size_mb in files:
        # Проверяем размер файла
        if size_mb > max_size_mb:
            oversized_files.append((file_path.name, size_mb))
            print(f"⚠️  Файл слишком большой ({size_mb:.2f} МБ): {file_path.name}")
            continue
        
        # Если достигли лимита файлов в папке, создаем новую
        if batch_file_count >= files_per_batch:
            current_batch += 1
            batch_file_count = 0
            batch_dir = output_dir / f"batch_{current_batch:03d}"
            batch_dir.mkdir(exist_ok=True)
            print(f"✅ Папка batch_{current_batch-1:03d} готова ({files_per_batch} файлов)")
        
        # Копируем файл
        dest_path = batch_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        
        copied_files += 1
        batch_file_count += 1
    
    # Финальное сообщение для последней папки
    if batch_file_count > 0:
        print(f"✅ Папка batch_{current_batch:03d} готова ({batch_file_count} файлов)")
    
    # Сохраняем отчет
    report = {
        "total_files": total_files,
        "copied_files": copied_files,
        "total_batches": current_batch,
        "files_per_batch": files_per_batch,
        "oversized_files": [
            {"name": name, "size_mb": size} 
            for name, size in oversized_files
        ]
    }
    
    report_path = output_dir / "upload_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Создаем текстовую инструкцию
    premium_status = "✅ TELEGRAM PREMIUM" if max_size_mb > 50 else "⚪ Обычный аккаунт"
    
    instructions = f"""
╔═══════════════════════════════════════════════════════════╗
║         ИНСТРУКЦИЯ ПО ЗАГРУЗКЕ В TELEGRAM BOT             ║
╚═══════════════════════════════════════════════════════════╝

👤 СТАТУС: {premium_status}
   Лимит размера файла: {max_size_mb} МБ

📊 СТАТИСТИКА:
   • Всего файлов обработано: {total_files}
   • Успешно скопировано: {copied_files}
   • Создано папок: {current_batch}
   • Файлов слишком больших: {len(oversized_files)}

📁 СТРУКТУРА:
   • Файлы разложены по папкам batch_001, batch_002, и т.д.
   • В каждой папке максимум {files_per_batch} файлов
   • Все файлы проверены на размер (<{max_size_mb} МБ)

📤 КАК ЗАГРУЖАТЬ:

   1. Откройте папку batch_001
   2. Выделите все файлы (Ctrl+A)
   3. Перетащите их в чат с ботом (drag-and-drop)
   4. Дождитесь завершения загрузки
   5. Перейдите к следующей папке

⚠️  РЕКОМЕНДАЦИИ:
💎 TELEGRAM PREMIUM:
   • С Premium можно отправлять файлы до 4 ГБ
   • Бот должен использовать Local Bot API Server для приема больших файлов
   • Без Premium лимит: 2 ГБ для отправки, 50 МБ для приема ботом

   • Загружайте по одной папке за раз
   • Между папками делайте паузу 10-20 секунд
   • Проверяйте, что все файлы загрузились успешно
   • При ошибках попробуйте загрузить файлы по одному

"""
    
    if oversized_files:
        instructions += "\n🚨 БОЛЬШИЕ ФАЙЛЫ (требуют специальной обработки):\n\n"
        for name, size in oversized_files:
            instructions += f"   • {name} ({size:.2f} МБ)\n"
        instructions += "\n   Эти файлы нужно загружать через Telegram Premium\n"
        instructions += "   или использовать локальный Telegram Bot API сервер.\n"
    
    instructions_path = output_dir / "README.txt"
    with open(instructions_path, "w", encoding="utf-8") as f:
        f.write(instructions)
    
    # Финальный вывод
    print(f"\n{'='*60}")
    print(f"✅ ГОТОВО!")
    print(f"{'='*60}")
    print(f"   📂 Папка с файлами: {output_dir}")
    print(f"   📋 Отчет: {report_path}")
    print(f"   📄 Инструкция: {instructions_path}")
    print(f"   📊 Создано папок: {current_batch}")
    print(f"   ✅ Скопировано файлов: {copied_files}/{total_files}")
    
    if oversized_files:
        print(f"   ⚠️  Больших файлов пропущено: {len(oversized_files)}")
    
    print(f"\n💡 Откройте {instructions_path} для подробной инструкции")
    print(f"{'='*60}\n")


def main():
    """Главная функция"""
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   ОРГАНИЗАЦИЯ МУЗЫКИ ДЛЯ ЗАГРУЗКИ В TELEGRAM              ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    source_dir = Path(SOURCE_DIR)
    output_dir = Path(OUTPUT_DIR)
    
    print(f"📂 Исходная папка: {source_dir}")
    print(f"📂 Выходная папка: {output_dir}\n")
    
    # Собираем файлы
    print("🔍 Сканирование файлов...")
    files = collect_files(source_dir)
    
    if not files:
        print("❌ MP3 файлы не найдены!")
        return
    
    # Организуем файлы
    organize_files(files, output_dir, FILES_PER_BATCH, MAX_FILE_SIZE_MB)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
