#!/bin/bash
# ===========================================
#  TG Player - Docker Deployment Script
# ===========================================
# Использование:
#   ./deploy/docker-deploy.sh [prod|dev|stop|logs|status]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}  TG Player - Docker Deployment${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}\n"
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ═══════════════════════════════════════════
#  Команды
# ═══════════════════════════════════════════

deploy_prod() {
    print_header
    echo "Deploying PRODUCTION environment..."
    echo ""

    # Проверка .env
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        echo "Create it from .env.example:"
        echo "  cp .env.example .env"
        echo "  nano .env"
        exit 1
    fi
    print_status ".env file found"

    # Pull latest images
    print_status "Pulling latest base images..."
    docker compose -f docker-compose.prod.yml pull postgres

    # Build and start
    print_status "Building and starting services..."
    docker compose -f docker-compose.prod.yml up -d --build

    # Wait for health
    echo ""
    print_status "Waiting for services to be healthy..."
    sleep 5

    # Show status
    echo ""
    docker compose -f docker-compose.prod.yml ps

    echo ""
    print_status "Deployment complete!"
    echo ""
    echo "Services:"
    echo "  • API:    http://localhost:${API_PORT:-8000}"
    echo "  • WebApp: http://localhost:${WEBAPP_PORT:-5173}"
    echo ""
    echo "Logs:  ./deploy/docker-deploy.sh logs"
    echo "Stop:  ./deploy/docker-deploy.sh stop"
}

deploy_dev() {
    print_header
    echo "Starting DEVELOPMENT environment..."
    echo "(Only PostgreSQL in Docker)"
    echo ""

    docker compose -f docker-compose.dev.yml up -d

    echo ""
    print_status "PostgreSQL is running on localhost:5432"
    echo ""
    echo "Now start locally:"
    echo "  Terminal 1: python -m uvicorn api.main:app --reload --port 8000"
    echo "  Terminal 2: python bot/main.py"
    echo "  Terminal 3: cd webapp && npm run dev"
    echo ""
    echo "Or use: ./run_dev.bat (Windows)"
}

stop_services() {
    print_header
    echo "Stopping all services..."
    
    # Stop prod if running
    if docker compose -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
        docker compose -f docker-compose.prod.yml down
        print_status "Production services stopped"
    fi
    
    # Stop dev if running
    if docker compose -f docker-compose.dev.yml ps -q 2>/dev/null | grep -q .; then
        docker compose -f docker-compose.dev.yml down
        print_status "Development services stopped"
    fi
    
    echo ""
    print_status "All services stopped"
}

show_logs() {
    if docker compose -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
        docker compose -f docker-compose.prod.yml logs -f "$2"
    elif docker compose -f docker-compose.dev.yml ps -q 2>/dev/null | grep -q .; then
        docker compose -f docker-compose.dev.yml logs -f "$2"
    else
        print_error "No services running"
    fi
}

show_status() {
    print_header
    
    echo "Production services:"
    docker compose -f docker-compose.prod.yml ps 2>/dev/null || echo "  Not running"
    
    echo ""
    echo "Development services:"
    docker compose -f docker-compose.dev.yml ps 2>/dev/null || echo "  Not running"
}

rebuild() {
    print_header
    echo "Rebuilding all images (no cache)..."
    
    docker compose -f docker-compose.prod.yml build --no-cache
    
    print_status "Rebuild complete"
    echo "Run './deploy/docker-deploy.sh prod' to start"
}

# ═══════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════

case "$1" in
    prod|production)
        deploy_prod
        ;;
    dev|development)
        deploy_dev
        ;;
    stop)
        stop_services
        ;;
    logs)
        show_logs "$@"
        ;;
    status|ps)
        show_status
        ;;
    rebuild)
        rebuild
        ;;
    *)
        print_header
        echo "Usage: $0 {prod|dev|stop|logs|status|rebuild}"
        echo ""
        echo "Commands:"
        echo "  prod      Deploy production (all services in Docker)"
        echo "  dev       Start dev environment (only PostgreSQL)"
        echo "  stop      Stop all services"
        echo "  logs      Show logs (optionally: logs api|bot|webapp)"
        echo "  status    Show running services"
        echo "  rebuild   Rebuild all images without cache"
        echo ""
        exit 1
        ;;
esac
