#!/usr/bin/env python3
"""
Миграция данных из SQLite в PostgreSQL для Docker.

Использование:
  1. Убедитесь что Docker контейнеры запущены:
     docker compose -f docker-compose.prod.yml up -d postgres
  
  2. Запустите скрипт:
     python scripts/migrate_sqlite_to_postgres.py
  
  3. Или передайте пути явно:
     python scripts/migrate_sqlite_to_postgres.py --sqlite tg_player.db --postgres "postgresql://..."
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def migrate_data(sqlite_path: str, postgres_url: str, dry_run: bool = False):
    """Мигрирует все данные из SQLite в PostgreSQL"""
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text, inspect
    
    print(f"\n{'='*60}")
    print("  Миграция данных SQLite -> PostgreSQL")
    print(f"{'='*60}\n")
    
    # Создаём подключения
    sqlite_url = f"sqlite+aiosqlite:///{sqlite_path}"
    print(f"📂 SQLite:    {sqlite_path}")
    print(f"🐘 PostgreSQL: {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")
    
    sqlite_engine = create_async_engine(sqlite_url, echo=False)
    postgres_engine = create_async_engine(postgres_url, echo=False)
    
    SQLiteSession = sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    PostgresSession = sessionmaker(postgres_engine, class_=AsyncSession, expire_on_commit=False)
    
    # Порядок таблиц важен из-за foreign keys
    tables_order = [
        'users',
        'tracks', 
        'track_enrichments',
        'albums',
        'album_tracks',
        'user_library',
        'user_channels',
        'playlists',
        'playlist_tracks',
        'playlist_subscriptions',
        'play_history',
    ]
    
    stats = {}
    
    try:
        async with sqlite_engine.connect() as sqlite_conn:
            async with postgres_engine.connect() as postgres_conn:
                
                # Получаем список существующих таблиц в SQLite
                result = await sqlite_conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                )
                existing_tables = {row[0] for row in result.fetchall()}
                print(f"\n📋 Таблицы в SQLite: {', '.join(sorted(existing_tables))}")
                
                # Проверяем PostgreSQL
                pg_result = await postgres_conn.execute(
                    text("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                    """)
                )
                pg_tables = {row[0] for row in pg_result.fetchall()}
                print(f"📋 Таблицы в PostgreSQL: {', '.join(sorted(pg_tables))}")
                
                if not pg_tables:
                    print("\n⚠️  PostgreSQL база пустая! Таблицы будут созданы автоматически при запуске API.")
                    print("   Запустите: docker compose -f docker-compose.prod.yml up api")
                    print("   Затем перезапустите этот скрипт.")
                    return
                
                print(f"\n{'─'*60}")
                print("  Начинаем миграцию данных...")
                print(f"{'─'*60}\n")
                
                for table in tables_order:
                    if table not in existing_tables:
                        print(f"⏭️  {table}: пропущена (нет в SQLite)")
                        continue
                    
                    if table not in pg_tables:
                        print(f"⏭️  {table}: пропущена (нет в PostgreSQL)")
                        continue
                    
                    # Получаем данные из SQLite
                    try:
                        result = await sqlite_conn.execute(text(f"SELECT * FROM {table}"))
                        rows = result.fetchall()
                        columns = result.keys()
                    except Exception as e:
                        print(f"❌ {table}: ошибка чтения - {e}")
                        continue
                    
                    if not rows:
                        print(f"⏭️  {table}: пустая")
                        stats[table] = 0
                        continue
                    
                    # Получаем колонки PostgreSQL таблицы
                    pg_cols_result = await postgres_conn.execute(
                        text(f"""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = '{table}' AND table_schema = 'public'
                        """)
                    )
                    pg_columns = {row[0] for row in pg_cols_result.fetchall()}
                    
                    # Используем только общие колонки
                    common_columns = [c for c in columns if c in pg_columns]
                    
                    if not common_columns:
                        print(f"⚠️  {table}: нет общих колонок")
                        continue
                    
                    if dry_run:
                        print(f"🔍 {table}: {len(rows)} записей (dry-run)")
                        stats[table] = len(rows)
                        continue
                    
                    # Очищаем таблицу в PostgreSQL (TRUNCATE CASCADE для связанных таблиц)
                    # Используем DELETE для безопасности
                    try:
                        await postgres_conn.execute(text(f"DELETE FROM {table}"))
                    except Exception as e:
                        print(f"⚠️  {table}: не удалось очистить - {e}")
                    
                    # Вставляем данные
                    inserted = 0
                    errors = 0
                    
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        # Берём только общие колонки
                        filtered_dict = {k: v for k, v in row_dict.items() if k in common_columns}
                        
                        cols = ', '.join(filtered_dict.keys())
                        placeholders = ', '.join(f':{k}' for k in filtered_dict.keys())
                        
                        try:
                            await postgres_conn.execute(
                                text(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"),
                                filtered_dict
                            )
                            inserted += 1
                        except Exception as e:
                            errors += 1
                            if errors <= 3:
                                print(f"   ⚠️  Ошибка вставки в {table}: {e}")
                    
                    await postgres_conn.commit()
                    
                    status = "✅" if errors == 0 else "⚠️"
                    print(f"{status} {table}: {inserted} записей" + (f" ({errors} ошибок)" if errors else ""))
                    stats[table] = inserted
                
                # Сбрасываем sequences для автоинкремента
                print(f"\n{'─'*60}")
                print("  Обновление sequences...")
                print(f"{'─'*60}\n")
                
                sequences = [
                    ('tracks', 'tracks_id_seq', 'id'),
                    ('albums', 'albums_id_seq', 'id'),
                    ('playlists', 'playlists_id_seq', 'id'),
                    ('track_enrichments', 'track_enrichments_id_seq', 'id'),
                    ('album_tracks', 'album_tracks_id_seq', 'id'),
                    ('user_library', 'user_library_id_seq', 'id'),
                ]
                
                for table, seq, col in sequences:
                    if table in pg_tables:
                        try:
                            await postgres_conn.execute(
                                text(f"SELECT setval('{seq}', COALESCE((SELECT MAX({col}) FROM {table}), 1))")
                            )
                            print(f"✅ {seq}: обновлён")
                        except Exception as e:
                            print(f"⏭️  {seq}: пропущен - {e}")
                
                await postgres_conn.commit()
        
        # Итоги
        print(f"\n{'='*60}")
        print("  Миграция завершена!")
        print(f"{'='*60}")
        
        total = sum(stats.values())
        print(f"\n📊 Всего перенесено: {total} записей")
        for table, count in stats.items():
            if count > 0:
                print(f"   • {table}: {count}")
        
        print(f"\n✅ Перезапустите Docker контейнеры:")
        print("   docker compose -f docker-compose.prod.yml restart")
        
    except Exception as e:
        print(f"\n❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await sqlite_engine.dispose()
        await postgres_engine.dispose()
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Миграция данных из SQLite в PostgreSQL')
    parser.add_argument(
        '--sqlite', '-s',
        default='tg_player.db',
        help='Путь к SQLite файлу (default: tg_player.db)'
    )
    parser.add_argument(
        '--postgres', '-p',
        default='postgresql+asyncpg://postgres:postgres@localhost:5432/tg_player',
        help='PostgreSQL connection URL'
    )
    parser.add_argument(
        '--docker', '-d',
        action='store_true',
        help='Использовать Docker PostgreSQL (localhost:5432)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Только показать что будет перенесено'
    )
    
    args = parser.parse_args()
    
    sqlite_path = args.sqlite
    
    # Проверяем существование SQLite файла
    if not Path(sqlite_path).exists():
        # Ищем в корне проекта
        project_root = Path(__file__).parent.parent
        alt_path = project_root / sqlite_path
        if alt_path.exists():
            sqlite_path = str(alt_path)
        else:
            print(f"❌ SQLite файл не найден: {sqlite_path}")
            print(f"   Проверьте путь или укажите явно: --sqlite /path/to/tg_player.db")
            sys.exit(1)
    
    postgres_url = args.postgres
    
    print("\n" + "="*60)
    print("  SQLite -> PostgreSQL Migration Tool")  
    print("="*60)
    print(f"\nИсточник:  {sqlite_path}")
    print(f"Назначение: {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")
    
    if args.dry_run:
        print("\n⚠️  Режим dry-run: данные НЕ будут изменены")
    
    asyncio.run(migrate_data(sqlite_path, postgres_url, args.dry_run))


if __name__ == "__main__":
    main()
