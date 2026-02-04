#!/bin/bash
# Настройка тестового окружения на сервере
# Используется параллельно с основным приложением

set -e

STAGING_DIR="/opt/tg_player_test"
API_SERVICE="tg-player-api-test.service"
BOT_SERVICE="tg-player-bot-test.service"

echo "=== Setting up STAGING environment ==="

# 1. Создание папки если нет
if [ ! -d "$STAGING_DIR" ]; then
    echo "Создание директории $STAGING_DIR..."
    sudo mkdir -p $STAGING_DIR
    sudo chown $USER:$USER $STAGING_DIR
    git clone https://github.com/your-username/tg_player.git $STAGING_DIR
fi

cd $STAGING_DIR

# 2. Переключение на ветку dev
echo "Переключение на ветку dev..."
git checkout dev || git checkout -b dev

# 3. Настройка venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# 4. Настройка .env (если нет)
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Отредактируй $STAGING_DIR/.env!"
    echo "Поменяй BOT_TOKEN на ТЕСТОВОГО бота"
    echo "Поменяй PORT на 8001"
fi

# 5. Установка сервисов
echo "Копирование systemd сервисов..."
sudo cp deploy/$API_SERVICE /etc/systemd/system/
sudo cp deploy/$BOT_SERVICE /etc/systemd/system/
sudo systemctl daemon-reload

echo "=== Готово! ==="
echo "Для запуска:"
echo "sudo systemctl enable --now $API_SERVICE $BOT_SERVICE"
