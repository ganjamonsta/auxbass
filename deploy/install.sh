#!/bin/bash
# TG Player - Установка на Debian 12
# Запускать от root или через sudo

set -e

APP_DIR="/opt/tg_player"
APP_USER="tgplayer"

echo "=== TG Player Installation ==="

# 1. Установка зависимостей
echo "[1/6] Установка системных пакетов..."
apt update
apt install -y python3 python3-pip python3-venv git curl

# 2. Создание пользователя
echo "[2/6] Создание пользователя $APP_USER..."
id -u $APP_USER &>/dev/null || useradd -r -s /bin/false $APP_USER

# 3. Копирование файлов
echo "[3/6] Копирование файлов в $APP_DIR..."
mkdir -p $APP_DIR
cp -r . $APP_DIR/
chown -R $APP_USER:$APP_USER $APP_DIR

# 4. Создание виртуального окружения
echo "[4/6] Создание Python venv..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Создание .env если нет
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[5/6] Создание .env файла..."
    cp .env.example .env
    echo "⚠️  Отредактируй $APP_DIR/.env — добавь BOT_TOKEN!"
else
    echo "[5/6] .env уже существует"
fi

# 6. Установка systemd сервисов
echo "[6/6] Установка systemd сервисов..."
cp deploy/tg-player-bot.service /etc/systemd/system/
cp deploy/tg-player-api.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "=== Готово! ==="
echo ""
echo "Следующие шаги:"
echo "1. Отредактируй конфиг:    nano $APP_DIR/.env"
echo "2. Запусти бота:           systemctl start tg-player-bot"
echo "3. Запусти API:            systemctl start tg-player-api"
echo "4. Автозапуск:             systemctl enable tg-player-bot tg-player-api"
echo ""
echo "Логи:                      journalctl -u tg-player-bot -f"
