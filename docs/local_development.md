# 🛠️ Локальная разработка TG Player

## Проблема
Сейчас: код → сразу на прод → тестируешь на живых данных 💀

Надо так: код → тестируешь локально → всё ок → push → деплой ✅

---

## 🚀 Быстрый старт (один раз настроить)

### 1. Создай тестового бота

1. Открой [@BotFather](https://t.me/BotFather) 
2. `/newbot`
3. Назови его `TG Player Dev` (или как хочешь)
4. Username: `tg_player_dev_bot` (любой свободный)
5. **Сохрани токен!**

### 2. Создай локальный .env

```bash
# Скопируй пример
copy .env.example .env.local
```

Отредактируй `.env.local`:
```env
# Telegram Bot - ТЕСТОВЫЙ бот для разработки!
BOT_TOKEN=123456:ABC-DEF_your_dev_bot_token
BOT_USERNAME=tg_player_dev_bot

# Локальная база (SQLite - проще всего)
DATABASE_URL=sqlite+aiosqlite:///./tg_player_dev.db

# Локальные адреса
API_HOST=0.0.0.0
API_PORT=8000
API_URL=http://localhost:8000

# Для фронта используем ngrok или localhost
WEBAPP_URL=http://localhost:5173

# Можно такой же как на проде
SECRET_KEY=dev-secret-key-12345
LASTFM_API_KEY=твой_ключ
```

### 3. Запуск локально

**Вариант А: SQLite (проще всего)**
```bash
# Терминал 1 - API
python -m uvicorn api.main:app --reload --port 8000

# Терминал 2 - Bot  
python bot/main.py

# Терминал 3 - Frontend
cd webapp && npm run dev
```

**Вариант Б: PostgreSQL (как на проде)**
```bash
# Поднять только базу
docker-compose up -d postgres

# Дальше как в варианте А
```

---

## 📋 Ежедневный рабочий процесс

### Утром: начинаем работу
```bash
# 1. Обновить код (если работаешь с нескольких мест)
git pull

# 2. Запустить локально
# Используй run_dev.bat (см. ниже)
```

### Разработка
1. Вносишь изменения в код
2. Тестируешь локально (через тестового бота)
3. Если всё ок - коммитишь:
```bash
git add .
git commit -m "Добавил фичу X"
```

### Когда готов к релизу
```bash
# Отправить на GitHub
git push

# Потом на сервере:
git pull
# и перезапустить сервисы
```

---

## 🔧 Полезные команды Git

### Сохранить изменения
```bash
git add .                          # Добавить все изменённые файлы
git commit -m "Описание что сделал" # Сохранить локально
git push                            # Отправить на GitHub
```

### Получить изменения
```bash
git pull                            # Скачать с GitHub
```

### Посмотреть статус
```bash
git status                          # Что изменено?
git diff                            # Какие именно изменения?
git log --oneline -10              # Последние 10 коммитов
```

### Если накосячил
```bash
git checkout -- filename            # Откатить один файл
git reset --hard                    # Откатить ВСЁ (осторожно!)
```

---

## 🌐 Как тестировать Mini App локально

Mini App работает внутри Telegram, поэтому нужен публичный URL.

### Вариант 1: ngrok (рекомендую)
```bash
# Установи ngrok: https://ngrok.com/download
ngrok http 5173
```
Получишь URL типа `https://abc123.ngrok.io` - его поставь в BotFather для тестового бота.

### Вариант 2: Тестировать без Telegram
Просто открой `http://localhost:5173` в браузере. Большинство функций работает.

---

## 📁 Структура .env файлов

```
.env.example    - Пример (в git, без секретов)
.env.local      - Для локальной разработки (НЕ в git!)
.env            - Для прода (НЕ в git!)
```

`.gitignore` уже настроен чтобы не пушить `.env` файлы.

---

## ❓ FAQ

### Зачем тестовый бот?
Чтобы не засирать прод-бота тестовыми данными и не ломать его для реальных пользователей.

### А база? Она же пустая локально
Да, это нормально. Закинь пару треков для тестов. Или скопируй базу с прода (см. ниже).

### Как скопировать базу с прода?
```bash
# На сервере
pg_dump -U postgres tg_player > backup.sql

# Скачай backup.sql к себе, потом локально:
docker-compose up -d postgres
docker exec -i tg_player_db psql -U postgres tg_player < backup.sql
```

### Hot reload работает?
Да! `--reload` в uvicorn и `npm run dev` автоматически перезапускают при изменениях.
