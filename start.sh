#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  TG Player - Pterodactyl Startup & Auto-Update Script
# ═══════════════════════════════════════════════════════════════════

echo "========================================================"
echo "          🎵 TG Player - Pterodactyl Starter            "
echo "========================================================"

# Allow git operations in Docker container directory
git config --global --add safe.directory "*" 2>/dev/null || true

# 1. Auto-update from Git
DEFAULT_REPO="https://github.com/ganjamonsta/auxbass.git"
REPO_URL="${GIT_ADDRESS:-$DEFAULT_REPO}"

if [ ! -d ".git" ]; then
    echo "📦 [1/3] Папка .git не найдена. Подключаем репозиторий ($REPO_URL)..."
    git init || true
    git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL" || true
    git fetch origin 2>/dev/null || true
    
    # Try main or master
    BRANCH="main"
    git show-ref --verify --quiet refs/remotes/origin/main || BRANCH="master"
    
    echo "⬇️ Синхронизируем код с веткой $BRANCH..."
    git checkout -B "$BRANCH" "origin/$BRANCH" 2>/dev/null || git reset --mixed "origin/$BRANCH" 2>/dev/null || true
else
    echo "📦 [1/3] Проверка обновлений Git..."
    git fetch origin 2>/dev/null || true
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
    echo "⬇️ Подтягиваем изменения из ветки: $CURRENT_BRANCH..."
    git pull origin "$CURRENT_BRANCH" 2>/dev/null || true
fi

# 2. Update Python dependencies
if [ -f "requirements.txt" ]; then
    echo "🐍 [2/3] Обновление зависимостей Python..."
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
echo "🚀 Запуск приложения (start.py)..."
exec python start.py
