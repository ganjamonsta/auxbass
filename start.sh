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

# 1. Run updater
if [ -f "update.sh" ]; then
    bash update.sh
fi

# 2. Launch Application (FastAPI + WebApp Static + Telegram Bot)
echo "🚀 Запуск TG Player (start.py)..."
exec python start.py

