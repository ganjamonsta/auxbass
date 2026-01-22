# TG Music Player — Спецификация проекта

## 🎯 Концепция

Веб-плеер для Telegram в формате Mini App, который решает проблему отсутствия плейлистов и удобного управления музыкой в Telegram.

### Ключевая идея
- Бот принимает аудиофайлы от пользователя
- **НЕ скачивает музыку на сервер** — использует Telegram как хранилище
- Сохраняет только метаданные и `file_id` в базе данных
- Воспроизведение через Telegram Mini App напрямую из серверов Telegram

---

## 📋 Требования

### Целевая аудитория
- Изначально: личное использование (single-user)
- Потенциально: публичный сервис с монетизацией

### Технический стек
| Компонент | Технология |
|-----------|------------|
| Бот | Python + aiogram 3.x |
| База данных | PostgreSQL / SQLite |
| Mini App Frontend | Vue.js / React + Tailwind CSS |
| API для Mini App | FastAPI |
| Хостинг | VPS (свой сервер) |
| Домен | Есть |

### Инфраструктура
- ✅ Домен есть
- ✅ VPS сервер есть
- ⏸️ Lossless поддержка — placeholder на будущее (премиум)

---

## 🔧 Функциональность

### MVP (Phase 1)
- [ ] Приём аудиофайлов от пользователя
- [ ] Автоматическое извлечение ID3 тегов (исполнитель, название, альбом, жанр, длительность)
- [ ] Сохранение `file_id` + метаданных в БД
- [ ] Mini App с базовым плеером
- [ ] Создание/редактирование плейлистов
- [ ] Поиск по исполнителю, названию, жанру
- [ ] Базовое управление воспроизведением (play/pause/next/prev)

### Phase 2
- [ ] Ручное редактирование метаданных треков
- [ ] Сортировка и фильтрация библиотеки
- [ ] История прослушивания
- [ ] Очередь воспроизведения
- [ ] Shuffle / Repeat режимы

### Phase 3 (Монетизация)
- [ ] Публичные плейлисты с возможностью шаринга
- [ ] Lossless поддержка (премиум)
- [ ] Multi-user режим
- [ ] Донат-система

---

## 🏗️ Архитектура

### Схема работы без скачивания файлов

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Пользователь  │────▶│   Telegram Bot  │────▶│    Database     │
│  отправляет MP3 │     │  (aiogram)      │     │  (file_id +     │
└─────────────────┘     └────────┬────────┘     │   metadata)     │
                                 │              └─────────────────┘
                                 │
                        Извлекает file_id
                        + ID3 теги (через
                        Telegram API, без
                        скачивания полного
                        файла)
                                 │
                                 ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Mini App      │◀───▶│   FastAPI       │◀───▶│    Database     │
│   (Frontend)    │     │   Backend       │     │                 │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         │ Запрос файла
         ▼
┌─────────────────┐
│  Telegram CDN   │  ◀── Воспроизведение напрямую
│  (file storage) │      через getFile API
└─────────────────┘
```

### Критический момент: Воспроизведение без скачивания

**Как это работает:**

1. При получении аудио бот сохраняет `file_id` (уникальный ID файла в Telegram)
2. Когда Mini App хочет воспроизвести трек:
   - Frontend запрашивает URL у backend
   - Backend вызывает `bot.get_file(file_id)` → получает `file_path`
   - Формирует URL: `https://api.telegram.org/file/bot<TOKEN>/<file_path>`
   - Этот URL валиден ~1 час, можно кэшировать
3. Mini App воспроизводит аудио через `<audio>` элемент с этим URL

**⚠️ Ограничения Telegram API:**
- Максимальный размер файла для скачивания через Bot API: **20 MB**
- Для файлов >20 MB нужен MTProto (Telethon/Pyrogram) — усложняет архитектуру
- `file_path` URL валиден ограниченное время (~1 час)

---

## 📁 Структура проекта

```
tg_player/
├── bot/                      # Telegram Bot
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── audio.py         # Обработка аудио
│   │   └── commands.py      # Команды бота
│   ├── services/
│   │   ├── __init__.py
│   │   ├── metadata.py      # Извлечение ID3
│   │   └── database.py      # Работа с БД
│   └── models/
│       ├── __init__.py
│       └── track.py         # Модели данных
│
├── api/                      # FastAPI Backend
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── tracks.py        # CRUD треков
│   │   ├── playlists.py     # CRUD плейлистов
│   │   └── player.py        # Получение URL для воспроизведения
│   ├── services/
│   │   ├── __init__.py
│   │   └── telegram.py      # Работа с Telegram API
│   └── auth/
│       ├── __init__.py
│       └── webapp.py        # Валидация Telegram WebApp
│
├── webapp/                   # Mini App Frontend
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Player.vue
│   │   │   ├── TrackList.vue
│   │   │   ├── Playlist.vue
│   │   │   └── Search.vue
│   │   ├── stores/
│   │   │   ├── player.js    # Состояние плеера
│   │   │   └── library.js   # Библиотека треков
│   │   ├── api/
│   │   │   └── client.js    # API клиент
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
│
├── database/
│   ├── migrations/
│   └── schema.sql
│
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🗄️ Схема базы данных

```sql
-- Пользователи (для multi-user в будущем)
CREATE TABLE users (
    id BIGINT PRIMARY KEY,           -- Telegram user_id
    username VARCHAR(255),
    first_name VARCHAR(255),
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Треки
CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    file_id VARCHAR(255) NOT NULL,   -- Telegram file_id
    file_unique_id VARCHAR(255),     -- Уникальный ID файла
    
    -- Метаданные
    title VARCHAR(255),
    artist VARCHAR(255),
    album VARCHAR(255),
    genre VARCHAR(100),
    duration INTEGER,                 -- В секундах
    
    -- Telegram данные
    file_size INTEGER,
    mime_type VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Плейлисты
CREATE TABLE playlists (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,  -- Для шаринга (премиум)
    share_code VARCHAR(50) UNIQUE,    -- Код для шаринга
    created_at TIMESTAMP DEFAULT NOW()
);

-- Связь плейлистов и треков
CREATE TABLE playlist_tracks (
    playlist_id INTEGER REFERENCES playlists(id) ON DELETE CASCADE,
    track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
    position INTEGER,                  -- Порядок в плейлисте
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (playlist_id, track_id)
);

-- Индексы для поиска
CREATE INDEX idx_tracks_artist ON tracks(artist);
CREATE INDEX idx_tracks_title ON tracks(title);
CREATE INDEX idx_tracks_genre ON tracks(genre);
CREATE INDEX idx_tracks_user ON tracks(user_id);
```

---

## 🔑 Ключевые зависимости

### Bot (Python)
```
aiogram>=3.0
aiohttp
mutagen              # Для ID3 тегов
sqlalchemy[asyncio]
asyncpg              # PostgreSQL
python-dotenv
```

### API (Python)
```
fastapi
uvicorn
sqlalchemy[asyncio]
asyncpg
aiogram              # Для получения file URL
python-dotenv
```

### Frontend
```
vue@3
@vueuse/core
pinia               # State management
axios
tailwindcss
@vueuse/integrations  # Для Telegram WebApp SDK
```

---

## 🔐 Аутентификация Mini App

Telegram Mini Apps передают `initData` — подписанные данные о пользователе.

```python
# api/auth/webapp.py
import hmac
import hashlib
from urllib.parse import parse_qsl

def validate_webapp_data(init_data: str, bot_token: str) -> dict | None:
    """Валидация данных от Telegram Mini App"""
    parsed = dict(parse_qsl(init_data))
    
    check_hash = parsed.pop('hash', None)
    if not check_hash:
        return None
    
    # Сортируем и формируем строку
    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )
    
    # Создаём секретный ключ
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()
    
    # Проверяем подпись
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if calculated_hash == check_hash:
        return parsed
    return None
```

---

## ⚡ API Endpoints

### Треки
```
GET    /api/tracks              # Список треков пользователя
GET    /api/tracks/{id}         # Информация о треке
GET    /api/tracks/{id}/stream  # Получить URL для воспроизведения
PUT    /api/tracks/{id}         # Обновить метаданные
DELETE /api/tracks/{id}         # Удалить трек
GET    /api/tracks/search       # Поиск по библиотеке
```

### Плейлисты
```
GET    /api/playlists           # Список плейлистов
POST   /api/playlists           # Создать плейлист
GET    /api/playlists/{id}      # Плейлист с треками
PUT    /api/playlists/{id}      # Обновить плейлист
DELETE /api/playlists/{id}      # Удалить плейлист
POST   /api/playlists/{id}/tracks      # Добавить трек
DELETE /api/playlists/{id}/tracks/{track_id}  # Убрать трек
```

---

## 🚀 Команды для запуска

### Development
```bash
# База данных
docker-compose up -d postgres

# Bot
cd bot && python main.py

# API
cd api && uvicorn main:app --reload --port 8000

# Frontend
cd webapp && npm run dev
```

### Production
```bash
docker-compose up -d
```

---

## 📝 Команды бота

```
/start      - Начало работы, приветствие
/help       - Справка
/library    - Открыть Mini App с библиотекой
/stats      - Статистика (кол-во треков, плейлистов)
/export     - Экспорт библиотеки (JSON)
```

**При отправке аудио:**
- Бот автоматически сохраняет трек
- Отвечает с информацией о треке и кнопкой "Открыть плеер"

---

## ⚠️ Важные ограничения

1. **Размер файлов**: Bot API поддерживает файлы до 20 MB для скачивания. Для бОльших файлов нужен MTProto.

2. **Срок жизни URL**: URL для скачивания файла валиден ~1 час. Нужно кэшировать и обновлять.

3. **Rate limits**: Telegram API имеет лимиты на запросы. Нужен кэш для `file_path`.

4. **CORS**: Mini App работает в iframe, API должен разрешать CORS.

5. **HTTPS**: Mini App требует HTTPS для API.

---

## 🎨 UI/UX концепция Mini App

### Основные экраны
1. **Библиотека** — все треки с поиском и фильтрами
2. **Плейлисты** — список плейлистов
3. **Плейлист** — треки в плейлисте
4. **Плеер** — полноэкранный плеер (slide up)

### Плеер (всегда внизу)
- Мини-версия при навигации
- Полная версия при клике
- Обложка альбома (если есть) или placeholder
- Progress bar
- Play/Pause, Next, Previous
- Shuffle, Repeat

---

## 🏷️ Placeholder для будущего

### Lossless поддержка (премиум)
```python
# Placeholder в БД
class Track:
    # ...
    is_lossless: bool = False
    audio_format: str = "mp3"  # mp3, flac, wav, etc.
```

### Публичные плейлисты
```python
# Уже в схеме БД
is_public: bool = False
share_code: str  # Генерируется при публикации
```

---

## ✅ Готовность к разработке

- [x] Концепция определена
- [x] Стек выбран
- [x] Архитектура спроектирована
- [x] Ограничения учтены
- [x] Домен есть
- [x] Сервер есть
- [ ] **Следующий шаг: создание структуры проекта и базовой реализации**

---

## 🚦 Начать разработку

Скажи "поехали" и я создам полную структуру проекта с рабочим кодом для MVP.
