# Восстановление библиотеки после миграции на Docker

Если после миграции с systemd на Docker библиотека пустая - это значит, что данные 
остались в старой SQLite базе и не были перенесены в PostgreSQL.

## Быстрое решение

```bash
# 1. Убедитесь что Docker запущен
./manage.sh prod start

# 2. Подождите 10-15 секунд пока PostgreSQL поднимется
sleep 15

# 3. Мигрируйте данные из SQLite
./manage.sh migrate-data

# 4. Перезапустите сервисы
./manage.sh prod restart
```

## Что произошло?

При миграции с systemd на Docker:

1. **Локально (systemd)** вы использовали **SQLite**: `tg_player.db`
2. **Docker** использует **PostgreSQL** в контейнере с отдельным volume
3. **Данные не были автоматически перенесены** из SQLite в PostgreSQL

## Детальная инструкция

### Шаг 1: Проверьте наличие SQLite базы

```bash
ls -la tg_player.db
```

Если файл существует - в нём ваши данные.

### Шаг 2: Запустите Docker контейнеры

```bash
# Из папки проекта
cd /path/to/tg_player
docker compose -f docker-compose.prod.yml up -d
```

### Шаг 3: Дождитесь запуска PostgreSQL

```bash
# Проверьте статус
docker compose -f docker-compose.prod.yml ps

# Или
./manage.sh status
```

PostgreSQL должен показывать статус "healthy".

### Шаг 4: Запустите миграцию данных

```bash
# Через manage.sh
./manage.sh migrate-data

# Или напрямую через Python скрипт
python3 scripts/migrate_sqlite_to_postgres.py
```

### Шаг 5: Перезапустите сервисы

```bash
./manage.sh prod restart
```

### Шаг 6: Проверьте результат

Откройте веб-приложение и проверьте что библиотека загружается.

## Устранение проблем

### Python скрипт не работает

Установите зависимости:
```bash
pip install asyncpg aiosqlite sqlalchemy
```

### PostgreSQL недоступен

Проверьте что порт 5432 открыт:
```bash
docker exec tg_player_db pg_isready -U postgres
```

### Таблицы не созданы в PostgreSQL

Таблицы создаются автоматически при запуске API. Если их нет:
```bash
# Перезапустите API
docker compose -f docker-compose.prod.yml restart api

# Или запустите init.sql вручную
docker exec -i tg_player_db psql -U postgres -d tg_player < database/init.sql
```

### Конфликт данных

Если в PostgreSQL уже есть данные, скрипт их перезапишет.
Для безопасности сделайте бэкап:

```bash
# Бэкап PostgreSQL в Docker
docker exec tg_player_db pg_dump -U postgres tg_player > backup_postgres.sql

# Бэкап SQLite
cp tg_player.db backup_sqlite.db
```

## Предотвращение проблемы в будущем

После успешной миграции:

1. **Сохраните бэкап SQLite** на случай отката
2. **Можете удалить** `tg_player.db` когда убедитесь что всё работает
3. Убедитесь что `.env` использует правильный `DATABASE_URL` для Docker:
   ```
   # Для Docker - используется внутренний адрес
   # DATABASE_URL переопределяется в docker-compose.prod.yml
   ```
