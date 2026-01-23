#!/bin/bash
#
# TG Player - Auto Update Script
# Usage: ./update.sh [--no-restart] [--force]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/opt/tg_player"
WEBAPP_DIR="$PROJECT_DIR/webapp"

# Parse arguments
NO_RESTART=false
FORCE=false

for arg in "$@"; do
    case $arg in
        --no-restart)
            NO_RESTART=true
            ;;
        --force)
            FORCE=true
            ;;
    esac
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   TG Player Update Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd "$PROJECT_DIR"

# Check for updates
echo -e "\n${YELLOW}[1/5]${NC} Checking for updates..."
git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ] && [ "$FORCE" = false ]; then
    echo -e "${GREEN}✓ Already up to date!${NC}"
    exit 0
fi

# Show what's new
echo -e "\n${YELLOW}[2/5]${NC} New commits:"
git log --oneline HEAD..origin/main | head -10

# Pull changes
echo -e "\n${YELLOW}[3/5]${NC} Pulling changes..."
git pull --rebase origin main

# Check if webapp changed
WEBAPP_CHANGED=$(git diff --name-only $LOCAL $REMOTE | grep -c "^webapp/" || true)

if [ "$WEBAPP_CHANGED" -gt 0 ] || [ "$FORCE" = true ]; then
    echo -e "\n${YELLOW}[4/5]${NC} Building webapp..."
    cd "$WEBAPP_DIR"
    npm run build
    cd "$PROJECT_DIR"
else
    echo -e "\n${YELLOW}[4/5]${NC} Webapp unchanged, skipping build..."
fi

# Restart services
if [ "$NO_RESTART" = false ]; then
    echo -e "\n${YELLOW}[5/5]${NC} Restarting services..."
    
    # Check what changed to restart only needed services
    BOT_CHANGED=$(git diff --name-only $LOCAL $REMOTE | grep -c "^bot/" || true)
    API_CHANGED=$(git diff --name-only $LOCAL $REMOTE | grep -c -E "^(api/|shared/)" || true)
    
    if [ "$BOT_CHANGED" -gt 0 ] || [ "$FORCE" = true ]; then
        echo "  → Restarting bot..."
        sudo systemctl restart tg-player-bot
    fi
    
    if [ "$API_CHANGED" -gt 0 ] || [ "$WEBAPP_CHANGED" -gt 0 ] || [ "$FORCE" = true ]; then
        echo "  → Restarting API..."
        sudo systemctl restart tg-player-api
    fi
else
    echo -e "\n${YELLOW}[5/5]${NC} Skipping service restart (--no-restart)"
fi

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✓ Update complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Show service status
echo -e "\n${BLUE}Service status:${NC}"
systemctl is-active tg-player-bot && echo -e "  Bot: ${GREEN}running${NC}" || echo -e "  Bot: ${RED}stopped${NC}"
systemctl is-active tg-player-api && echo -e "  API: ${GREEN}running${NC}" || echo -e "  API: ${RED}stopped${NC}"
