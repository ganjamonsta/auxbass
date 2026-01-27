# TG Player 🎵

Веб-плеер для Telegram в формате Mini App. Позволяет собирать музыкальную библиотеку и слушать её через удобный интерфейс прямо в Telegram.

## ✨ Возможности

- 📤 Автоматическое добавление аудиофайлов, отправленных боту
- 🎵 Воспроизведение музыки напрямую из Telegram (без скачивания на сервер)
- � Автообогащение метаданных (Deezer, Last.fm)
- 💿 Группировка по альбомам и исполнителям
- 📁 Создание и управление плейлистами
- 🔍 Поиск по названию, артисту
- ✏️ Редактирование метаданных треков
- ☁️ Резервное копирование в личный Telegram канал
- 🔀 Shuffle и Repeat режимы

## 🏗️ Архитектура

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Telegram Bot  │────▶│    Database     │◀────│   FastAPI       │
│   (aiogram)     │     │   (PostgreSQL)  │     │   Backend       │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   Mini App      │
                                                │   (Vue.js)      │
                                                └─────────────────┘
```

**Ключевая особенность:** Бот не скачивает аудиофайлы. Он сохраняет только `file_id` и метаданные. Воспроизведение происходит напрямую с серверов Telegram.

## 🚀 Быстрый старт

### 1. Клонирование и настройка

```bash
cd tg_player
cp .env.example .env
```

Отредактируй `.env`:
```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tg_player
WEBAPP_URL=https://your-domain.com
```

### 2. Запуск с Docker

```bash
docker-compose up -d
```

### 3. Запуск для разработки

```bash
# Установка зависимостей Python
pip install -r requirements.txt

# Запуск базы данных
docker-compose up -d postgres

# Запуск бота (терминал 1)
python bot/main.py

# Запуск API (терминал 2)
cd api && uvicorn main:app --reload --port 8000

# Запуск фронтенда (терминал 3)
cd webapp && npm install && npm run dev
```

### 4. Настройка Mini App в BotFather

1. Открой [@BotFather](https://t.me/BotFather)
2. Выбери своего бота → Edit Bot → Bot Settings → Menu Button
3. Установи URL на `https://your-domain.com`

## 📁 Структура проекта

```
tg_player/
├── bot/                    # Telegram Bot (aiogram)
│   ├── handlers/
│   │   ├── commands.py     # /start, /help, /stats
│   │   ├── audio.py        # Обработка аудиофайлов
│   │   └── callbacks.py    # Inline кнопки
│   └── main.py
│
├── api/                    # FastAPI Backend
│   ├── routers/
│   │   ├── auth.py         # Валидация Telegram initData
│   │   ├── tracks.py       # CRUD треков
│   │   ├── playlists.py    # CRUD плейлистов
│   │   └── player.py       # Получение URL для воспроизведения
│   └── main.py
│
├── webapp/                 # Vue.js Mini App
│   ├── src/
│   │   ├── components/     # UI компоненты
│   │   ├── stores/         # Pinia stores
│   │   ├── api/            # API клиент
│   │   └── App.vue
│   └── package.json
│
├── shared/                 # Общий код
│   ├── config.py           # Конфигурация
│   ├── models.py           # SQLAlchemy модели
│   └── database.py         # Подключение к БД
│
├── database/
│   └── init.sql            # Схема базы данных
│
├── docker-compose.yml
├── Dockerfile.bot
├── Dockerfile.api
└── requirements.txt
```

## 🔧 API Endpoints

### Auth
- `POST /api/auth/validate` - Валидация Telegram initData
- `GET /api/auth/me` - Текущий пользователь

### Tracks
- `GET /api/tracks` - Список треков (с пагинацией и поиском)
- `GET /api/tracks/{id}` - Информация о треке
- `PUT /api/tracks/{id}` - Обновить метаданные
- `DELETE /api/tracks/{id}` - Удалить трек
- `GET /api/tracks/artists` - Список артистов
- `GET /api/tracks/genres` - Список жанров

### Playlists
- `GET /api/playlists` - Список плейлистов
- `POST /api/playlists` - Создать плейлист
- `GET /api/playlists/{id}` - Плейлист с треками
- `PUT /api/playlists/{id}` - Обновить плейлист
- `DELETE /api/playlists/{id}` - Удалить плейлист
- `POST /api/playlists/{id}/tracks` - Добавить трек
- `DELETE /api/playlists/{id}/tracks/{track_id}` - Убрать трек

### Player
- `GET /api/player/stream/{track_id}` - Получить URL для воспроизведения

## ⚠️ Ограничения

- **Стриминг файлов > 20 MB**: Telegram Bot API не позволяет скачивать файлы больше 20 MB через `getFile`. Такие треки отмечаются иконкой 📥 и размером — их можно скачать через меню трека (кнопка "Скачать"), но не стримить.
- **URL файлов**: Временные, валидны ~1 час (автоматически обновляются)

> 💡 **Философия проекта**: Использовать Telegram как бесплатное облачное хранилище. Все файлы хранятся в Telegram, на сервере только метаданные.

## 🔐 Безопасность

- Все запросы к API валидируются через Telegram initData
- HMAC-SHA256 подпись проверяется на бэкенде
- Пользователь может получить доступ только к своим данным

## 📝 Лицензия

MIT

## 🚧 Roadmap

- [ ] Публичные плейлисты с шарингом
- [ ] Lossless поддержка (FLAC, WAV)
- [ ] Рекомендации
- [ ] Донат-система
