#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  TG Player - Pterodactyl Updater (Startup Command 1)
# ═══════════════════════════════════════════════════════════════════

set -e

echo "========================================================"
echo "          🔄 TG Player - Auto Updater                   "
echo "========================================================"

# Disable interactive git prompts
export GIT_TERMINAL_PROMPT=0

# Allow git operations in Docker container directory
git config --global --add safe.directory "*" 2>/dev/null || true
git config --global init.defaultBranch main 2>/dev/null || true

# 1. Update repository from Git
DEFAULT_REPO="https://github.com/ganjamonsta/auxbass.git"

if [ -n "$GITHUB_TOKEN" ]; then
    REPO_URL="https://${GITHUB_TOKEN}@github.com/ganjamonsta/auxbass.git"
elif [ -n "$GIT_TOKEN" ]; then
    REPO_URL="https://${GIT_TOKEN}@github.com/ganjamonsta/auxbass.git"
else
    REPO_URL="${GIT_ADDRESS:-$DEFAULT_REPO}"
fi

echo "📦 [1/3] Обновление кода из Git..."
if [ ! -d ".git" ]; then
    git init 2>/dev/null || true
fi

git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL" 2>/dev/null || true

if git fetch origin main --depth=1 2>/dev/null || git fetch origin 2>/dev/null; then
    BRANCH="main"
    if git show-ref --verify --quiet refs/remotes/origin/main; then
        BRANCH="main"
    elif git show-ref --verify --quiet refs/remotes/origin/master; then
        BRANCH="master"
    fi
    git checkout -B "$BRANCH" "origin/$BRANCH" 2>/dev/null || git reset --hard "origin/$BRANCH" 2>/dev/null || true
    echo "✅ Исходный код обновлен!"
else
    echo "⚠️ Не удалось обновить через Git (нет сети или доступа), используем текущие файлы."
fi

# 2. Update Python dependencies
if [ -f "requirements.txt" ]; then
    echo "🐍 [2/3] Проверка зависимостей Python..."
    pip install --no-cache-dir -r requirements.txt 2>/dev/null || pip install -r requirements.txt || true
fi

# 3. Update WebApp Static Bundle
echo "🌐 [3/3] Проверка и обновление WebApp..."
TAR_URL_RELEASE="https://github.com/ganjamonsta/auxbass/releases/latest/download/webapp-dist.tar.gz"
TAR_URL_RAW="https://raw.githubusercontent.com/ganjamonsta/auxbass/release-dist/webapp-dist.tar.gz"
TEMP_TAR="/tmp/webapp-dist.tar.gz"

DOWNLOADED=0
# 1. Try downloading prebuilt release asset from GitHub Releases
if curl -fsSL -L "$TAR_URL_RELEASE" -o "$TEMP_TAR" 2>/dev/null && [ -s "$TEMP_TAR" ]; then
    echo "📦 Распаковка актуальной сборки WebApp из GitHub Releases..."
    tar -xzf "$TEMP_TAR" -C . 2>/dev/null || true
    rm -f "$TEMP_TAR"
    DOWNLOADED=1
    echo "✅ WebApp успешно обновлен из GitHub Releases!"
# 2. Fallback: Try downloading from release-dist branch
elif curl -fsSL -L "$TAR_URL_RAW" -o "$TEMP_TAR" 2>/dev/null && [ -s "$TEMP_TAR" ]; then
    echo "📦 Распаковка актуальной сборки WebApp из ветки release-dist..."
    tar -xzf "$TEMP_TAR" -C . 2>/dev/null || true
    rm -f "$TEMP_TAR"
    DOWNLOADED=1
    echo "✅ WebApp успешно обновлен из release-dist!"
fi

# Fallback: if no release tarball and dist is missing, build locally if node exists
if [ "$DOWNLOADED" -eq 0 ] && ([ ! -d "webapp/dist" ] || [ ! -f "webapp/dist/index.html" ]); then
    if command -v npm &> /dev/null; then
        echo "🔨 Сборка WebApp локально через npm..."
        (cd webapp && npm install && npm run build) || true
    else
        echo "ℹ️ WebApp сборка сохранена из текущего кеша."
    fi
fi

echo "========================================================"
echo "          ✅ Обновление успешно завершено!              "
echo "========================================================"
