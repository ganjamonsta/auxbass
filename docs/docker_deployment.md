# 🐳 Docker Deployment Guide

## Обзор архитектуры

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Host                           │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   WebApp    │  │     API     │  │    Telegram Bot     │  │
│  │   (nginx)   │  │  (FastAPI)  │  │     (aiogram)       │  │
│  │   :5173     │  │    :8000    │  │                     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          │                                   │
│                   ┌──────▼──────┐                            │
│                   │  PostgreSQL │                            │
│                   │    :5432    │                            │
│                   └─────────────┘                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Быстрый старт

### 1. Подготовка

```bash
# Клонируй репозиторий (если ещё нет)
git clone https://github.com/your-repo/tg_player.git
cd tg_player

# Создай .env файл
cp .env.example .env
nano .env  # Заполни BOT_TOKEN, DB_PASSWORD, SECRET_KEY
```

### 2. Запуск Production

```bash
# Сделай скрипт исполняемым
chmod +x deploy/docker-deploy.sh

# Запусти всё
./deploy/docker-deploy.sh prod
```

Готово! Сервисы запущены:
- **API**: http://localhost:8000
- **WebApp**: http://localhost:5173

### 3. Управление

```bash
# Статус сервисов
./deploy/docker-deploy.sh status

# Логи (все сервисы)
./deploy/docker-deploy.sh logs

# Логи конкретного сервиса
./deploy/docker-deploy.sh logs api
./deploy/docker-deploy.sh logs bot
./deploy/docker-deploy.sh logs webapp

# Остановка
./deploy/docker-deploy.sh stop

# Пересборка (после изменений кода)
./deploy/docker-deploy.sh rebuild
./deploy/docker-deploy.sh prod
```

---

## Миграция с systemd на Docker

### Шаг 1: Остановить systemd сервисы

```bash
sudo systemctl stop tg-player-api tg-player-bot tg-player-webapp
sudo systemctl disable tg-player-api tg-player-bot tg-player-webapp
```

### Шаг 2: Бэкап базы данных (если PostgreSQL уже есть)

```bash
# Если БД на хосте
pg_dump -U postgres tg_player > backup.sql

# Или если в другом Docker
docker exec tg_player_db pg_dump -U postgres tg_player > backup.sql
```

### Шаг 3: Запустить Docker

```bash
cd /opt/tg_player
git pull
./deploy/docker-deploy.sh prod
```

### Шаг 4: Восстановить данные (если нужно)

```bash
# Подождать пока PostgreSQL поднимется
sleep 10

# Восстановить базу
cat backup.sql | docker exec -i tg_player_db psql -U postgres tg_player
```

### Шаг 5: Проверить

```bash
./deploy/docker-deploy.sh status
./deploy/docker-deploy.sh logs
```

---

## Структура файлов

```
tg_player/
├── docker-compose.prod.yml    # Production (все сервисы)
├── docker-compose.dev.yml     # Development (только БД)
├── docker-compose.yml         # Legacy (можно удалить)
│
├── Dockerfile.api             # API image
├── Dockerfile.bot             # Bot image  
├── Dockerfile.webapp          # WebApp image (multi-stage)
│
├── .env.example               # Пример переменных
├── .env                       # Твои настройки (не в git!)
│
└── deploy/
    ├── docker-deploy.sh       # Скрипт деплоя
    ├── nginx.webapp.conf      # Nginx конфиг для WebApp
    └── *.service              # Старые systemd файлы (legacy)
```

---

## Окружения

### Production (`docker-compose.prod.yml`)
- Все 4 сервиса в Docker
- PostgreSQL с healthcheck
- nginx для статики WebApp
- Автоматический рестарт

### Development (`docker-compose.dev.yml`)
- Только PostgreSQL в Docker
- API, Bot, WebApp запускаются локально
- Hot-reload при изменении кода

```bash
# Dev: запустить только БД
./deploy/docker-deploy.sh dev

# Локально:
python -m uvicorn api.main:app --reload --port 8000
python bot/main.py
cd webapp && npm run dev
```

---

## Обновление кода

```bash
cd /opt/tg_player

# Получить изменения
git pull

# Пересобрать и перезапустить
./deploy/docker-deploy.sh rebuild
./deploy/docker-deploy.sh prod
```

Или одной командой:
```bash
git pull && docker compose -f docker-compose.prod.yml up -d --build
```

---

## Troubleshooting

### Контейнер не запускается
```bash
# Посмотреть логи
docker logs tg_player_api
docker logs tg_player_bot

# Проверить .env
cat .env | grep -E '^[A-Z]'
```

### База не подключается
```bash
# Проверить что PostgreSQL жив
docker exec tg_player_db pg_isready

# Проверить подключение
docker exec -it tg_player_db psql -U postgres -d tg_player -c "SELECT 1"
```

### Порт занят
```bash
# Найти что занимает порт
sudo lsof -i :8000
sudo lsof -i :5173

# Или изменить порты в .env
API_PORT=8001
WEBAPP_PORT=3000
```

### Очистить всё и начать заново
```bash
# Остановить и удалить контейнеры + volumes
docker compose -f docker-compose.prod.yml down -v

# Удалить images
docker rmi tg_player-api tg_player-bot tg_player-webapp

# Запустить заново
./deploy/docker-deploy.sh prod
```

---

## Автозапуск при перезагрузке

Docker сам перезапустит контейнеры (`restart: unless-stopped`).

Но если Docker не запущен при старте системы:
```bash
sudo systemctl enable docker
```
