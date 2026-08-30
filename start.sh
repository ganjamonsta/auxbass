#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  TG Player - Pterodactyl Startup & Auto-Update Script
# ═══════════════════════════════════════════════════════════════════
set -e

echo "========================================================"
echo "          🎵 TG Player - Pterodactyl Starter            "
echo "========================================================"

# Allow git operations in Docker container directory
git config --global --add safe.directory "*" 2>/dev/null || true
git config --global init.defaultBranch main 2>/dev/null || true

# 1. Auto-update from Git
DEFAULT_REPO="https://github.com/ganjamonsta/auxbass.git"
REPO_URL="${GIT_ADDRESS:-$DEFAULT_REPO}"

echo "📦 [1/3] Проверка обновлений Git ($REPO_URL)..."
if [ ! -d ".git" ]; then
    git init
fi

git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL" || true
echo "⬇️ Подтягиваем свежий код из репозитория..."
git fetch origin main || git fetch origin master || git fetch origin || true

BRANCH="main"
if git show-ref --verify --quiet refs/remotes/origin/main; then
    BRANCH="main"
elif git show-ref --verify --quiet refs/remotes/origin/master; then
    BRANCH="master"
fi

git checkout -B "$BRANCH" "origin/$BRANCH" 2>/dev/null || git reset --hard "origin/$BRANCH" 2>/dev/null || git pull origin "$BRANCH" 2>/dev/null || true

# 2. Update Python dependencies
if [ -f "requirements.txt" ]; then
    echo "🐍 [2/3] Установка/обновление зависимостей Python..."
    pip install --no-cache-dir -r requirements.txt || pip install -r requirements.txt || true
fi

# 3. Build WebApp if Node.js / npm is installed and dist is missing
if command -v npm &> /dev/null && [ -d "webapp" ]; then
    echo "🌐 [3/3] Проверка сборки WebApp..."
    if [ ! -d "webapp/dist" ]; then
        echo "🔨 Собираем фронтенд WebApp..."
        (cd webapp && npm install && npm run build) || true
    fi
fi

# 4. Launch Application (FastAPI + WebApp Static + Telegram Bot)
echo "🚀 Запуск TG Player (start.py)..."
exec python start.py
