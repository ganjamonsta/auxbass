#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  TG Player - Pterodactyl Startup & Auto-Update Script
# ═══════════════════════════════════════════════════════════════════

echo "========================================================"
echo "          🎵 TG Player - Pterodactyl Starter            "
echo "========================================================"

# Disable interactive git prompts to prevent server hang
export GIT_TERMINAL_PROMPT=0

# Allow git operations in Docker container directory
git config --global --add safe.directory "*" 2>/dev/null || true
git config --global init.defaultBranch main 2>/dev/null || true

# 1. Auto-update from Git
DEFAULT_REPO="https://github.com/ganjamonsta/auxbass.git"

# Support GITHUB_TOKEN or GIT_TOKEN for private repos
if [ -n "$GITHUB_TOKEN" ]; then
    REPO_URL="https://${GITHUB_TOKEN}@github.com/ganjamonsta/auxbass.git"
elif [ -n "$GIT_TOKEN" ]; then
    REPO_URL="https://${GIT_TOKEN}@github.com/ganjamonsta/auxbass.git"
else
    REPO_URL="${GIT_ADDRESS:-$DEFAULT_REPO}"
fi

echo "📦 [1/3] Проверка обновлений Git..."
if [ ! -d ".git" ]; then
    git init 2>/dev/null || true
fi

git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL" 2>/dev/null || true

echo "⬇️ Подтягиваем изменения с GitHub..."
if git fetch origin main --depth=1 2>/dev/null || git fetch origin 2>/dev/null; then
    BRANCH="main"
    if git show-ref --verify --quiet refs/remotes/origin/main; then
        BRANCH="main"
    elif git show-ref --verify --quiet refs/remotes/origin/master; then
        BRANCH="master"
    fi
    git checkout -B "$BRANCH" "origin/$BRANCH" 2>/dev/null || git reset --hard "origin/$BRANCH" 2>/dev/null || true
    echo "✅ Код успешно обновлен!"
else
    echo "⚠️ Не удалось обновить через Git (приватный репозиторий или нет доступа)."
    echo "ℹ️ Запускаем сервер на текущих локальных файлах."
fi

# 2. Update Python dependencies
if [ -f "requirements.txt" ]; then
    echo "🐍 [2/3] Проверка зависимостей Python..."
    pip install --no-cache-dir -r requirements.txt || pip install -r requirements.txt || true
fi

# 3. Build WebApp if needed
if [ -d "webapp" ]; then
    echo "🌐 [3/3] Проверка сборки WebApp..."
    
    # If npm is missing and dist is missing, install portable Node.js
    if ! command -v npm &> /dev/null && [ ! -d "webapp/dist" ]; then
        echo "📦 Установка портативного Node.js (v20)..."
        mkdir -p "$HOME/.local"
        curl -fsSL https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-x64.tar.xz | tar -xJ -C "$HOME/.local" 2>/dev/null || true
        if [ -d "$HOME/.local/node-v20.18.0-linux-x64" ]; then
            rm -rf "$HOME/.local/node" 2>/dev/null || true
            mv "$HOME/.local/node-v20.18.0-linux-x64" "$HOME/.local/node"
        fi
        if [ -d "$HOME/.local/node/bin" ]; then
            export PATH="$HOME/.local/node/bin:$PATH"
        fi
    fi

    if [ ! -d "webapp/dist" ] || [ ! -f "webapp/dist/index.html" ]; then
        if command -v npm &> /dev/null; then
            echo "🔨 Собираем фронтенд WebApp..."
            (cd webapp && npm install && npm run build) || true
        fi
    fi
fi

# 4. Launch Application (FastAPI + WebApp Static + Telegram Bot)
echo "🚀 Запуск TG Player (start.py)..."
exec python start.py
