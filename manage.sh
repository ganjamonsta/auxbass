#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  TG Player Manager v2.0
# ═══════════════════════════════════════════════════════════════════════════════
#  Универсальный менеджер для управления dev и prod окружениями
#
#  Использование:
#    ./manage.sh                    # Интерактивное меню
#    ./manage.sh <command> [args]   # CLI режим
#
#  Примеры:
#    ./manage.sh status             # Статус всех сервисов
#    ./manage.sh prod start         # Запустить prod
#    ./manage.sh dev logs api       # Логи API в dev
#    ./manage.sh update             # Обновить код и пересобрать
#    ./manage.sh switch dev         # Переключиться на dev
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Файлы конфигурации
PROD_COMPOSE="docker-compose.prod.yml"
DEV_COMPOSE="docker-compose.dev.yml"
STATE_FILE=".manager_state"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
DIM='\033[2m'
NC='\033[0m'
BOLD='\033[1m'

# Иконки
ICON_OK="✓"
ICON_FAIL="✗"
ICON_WARN="⚠"
ICON_INFO="ℹ"
ICON_ROCKET="🚀"
ICON_DOCKER="🐳"
ICON_GIT="📦"
ICON_DB="🗄"
ICON_API="⚡"
ICON_BOT="🤖"
ICON_WEB="🌐"

# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

print_header() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                               ║"
    echo "║   ${WHITE}████████╗ ██████╗     ██████╗ ██╗      █████╗ ██╗   ██╗███████╗██████╗${CYAN}    ║"
    echo "║   ${WHITE}╚══██╔══╝██╔════╝     ██╔══██╗██║     ██╔══██╗╚██╗ ██╔╝██╔════╝██╔══██╗${CYAN}   ║"
    echo "║   ${WHITE}   ██║   ██║  ███╗    ██████╔╝██║     ███████║ ╚████╔╝ █████╗  ██████╔╝${CYAN}   ║"
    echo "║   ${WHITE}   ██║   ██║   ██║    ██╔═══╝ ██║     ██╔══██║  ╚██╔╝  ██╔══╝  ██╔══██╗${CYAN}   ║"
    echo "║   ${WHITE}   ██║   ╚██████╔╝    ██║     ███████╗██║  ██║   ██║   ███████╗██║  ██║${CYAN}   ║"
    echo "║   ${WHITE}   ╚═╝    ╚═════╝     ╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝${CYAN}   ║"
    echo "║                                                                               ║"
    echo "║                         ${WHITE}${BOLD}Server Manager v2.0${NC}${CYAN}                                 ║"
    echo "║                                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_mini_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  ${WHITE}${BOLD}TG Player Manager${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"
}

log_info() { echo -e "${BLUE}${ICON_INFO}${NC} $1"; }
log_ok() { echo -e "${GREEN}${ICON_OK}${NC} $1"; }
log_warn() { echo -e "${YELLOW}${ICON_WARN}${NC} $1"; }
log_error() { echo -e "${RED}${ICON_FAIL}${NC} $1"; }
log_step() { echo -e "${PURPLE}→${NC} $1"; }

# Получить текущую git ветку
get_branch() {
    git branch --show-current 2>/dev/null || echo "unknown"
}

# Получить короткий hash коммита
get_commit() {
    git rev-parse --short HEAD 2>/dev/null || echo "unknown"
}

# Получить время последнего коммита
get_commit_time() {
    git log -1 --format="%cr" 2>/dev/null || echo "unknown"
}

# Проверить наличие несохраненных изменений
has_changes() {
    [ -n "$(git status --porcelain 2>/dev/null)" ]
}

# Проверить есть ли обновления на remote
has_updates() {
    git fetch --quiet 2>/dev/null
    local LOCAL=$(git rev-parse @ 2>/dev/null)
    local REMOTE=$(git rev-parse @{u} 2>/dev/null)
    [ "$LOCAL" != "$REMOTE" ]
}

# Проверить запущен ли Docker
check_docker() {
    if ! docker info &>/dev/null; then
        log_error "Docker не запущен!"
        return 1
    fi
    return 0
}

# Получить статус контейнера
container_status() {
    local container=$1
    local status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
    local health=$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "")
    
    case "$status" in
        running)
            if [ "$health" = "healthy" ]; then
                echo -e "${GREEN}● running (healthy)${NC}"
            elif [ "$health" = "unhealthy" ]; then
                echo -e "${RED}● running (unhealthy)${NC}"
            else
                echo -e "${GREEN}● running${NC}"
            fi
            ;;
        exited)
            echo -e "${RED}○ stopped${NC}"
            ;;
        restarting)
            echo -e "${YELLOW}◐ restarting${NC}"
            ;;
        *)
            echo -e "${DIM}○ not created${NC}"
            ;;
    esac
}

# Проверить какое окружение запущено
get_running_env() {
    local prod_running=false
    local dev_running=false
    
    if docker compose -f "$PROD_COMPOSE" ps -q 2>/dev/null | grep -q .; then
        prod_running=true
    fi
    
    if docker compose -f "$DEV_COMPOSE" ps -q 2>/dev/null | grep -q .; then
        dev_running=true
    fi
    
    if $prod_running && $dev_running; then
        echo "both"
    elif $prod_running; then
        echo "prod"
    elif $dev_running; then
        echo "dev"
    else
        echo "none"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
#  STATUS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

show_status() {
    print_mini_header
    
    # Git info
    echo -e "${BOLD}${ICON_GIT} Git Status${NC}"
    echo -e "  Branch:  ${CYAN}$(get_branch)${NC}"
    echo -e "  Commit:  ${DIM}$(get_commit)${NC} ($(get_commit_time))"
    
    if has_changes; then
        echo -e "  Changes: ${YELLOW}uncommitted changes${NC}"
    else
        echo -e "  Changes: ${GREEN}clean${NC}"
    fi
    
    if has_updates 2>/dev/null; then
        echo -e "  Remote:  ${YELLOW}updates available${NC}"
    else
        echo -e "  Remote:  ${GREEN}up to date${NC}"
    fi
    
    echo ""
    
    # Docker status
    echo -e "${BOLD}${ICON_DOCKER} Docker Services${NC}"
    
    local running_env=$(get_running_env)
    
    echo ""
    echo -e "  ${BOLD}Production:${NC}"
    echo -e "    ${ICON_DB}  postgres   $(container_status tg_player_db)"
    echo -e "    ${ICON_API} api        $(container_status tg_player_api)"
    echo -e "    ${ICON_BOT} bot        $(container_status tg_player_bot)"
    echo -e "    ${ICON_WEB} webapp     $(container_status tg_player_webapp)"
    
    echo ""
    echo -e "  ${BOLD}Development:${NC}"
    echo -e "    ${ICON_DB}  postgres   $(container_status tg_player_db_dev)"
    
    echo ""
    
    # Resource usage
    echo -e "${BOLD}📊 Resource Usage${NC}"
    docker stats --no-stream --format "  {{.Name}}: CPU {{.CPUPerc}}, Mem {{.MemUsage}}" 2>/dev/null | head -5 || echo "  No containers running"
    
    echo ""
}

show_quick_status() {
    local running=$(get_running_env)
    local branch=$(get_branch)
    
    echo -e "${CYAN}TG Player${NC} | Branch: ${CYAN}$branch${NC} | Running: ${GREEN}$running${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ENVIRONMENT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

start_prod() {
    log_step "Starting production environment..."
    
    # Check .env
    if [ ! -f ".env" ]; then
        log_error ".env file not found! Copy from .env.example"
        return 1
    fi
    
    docker compose -f "$PROD_COMPOSE" up -d --build
    
    echo ""
    log_ok "Production started!"
    echo ""
    echo -e "  ${ICON_API} API:    ${CYAN}http://localhost:${API_PORT:-8000}${NC}"
    echo -e "  ${ICON_WEB} WebApp: ${CYAN}http://localhost:${WEBAPP_PORT:-5173}${NC}"
}

stop_prod() {
    log_step "Stopping production environment..."
    docker compose -f "$PROD_COMPOSE" down
    log_ok "Production stopped"
}

restart_prod() {
    log_step "Restarting production environment..."
    docker compose -f "$PROD_COMPOSE" restart
    log_ok "Production restarted"
}

start_dev() {
    log_step "Starting development environment (PostgreSQL only)..."
    docker compose -f "$DEV_COMPOSE" up -d
    
    echo ""
    log_ok "Development database started!"
    echo ""
    echo -e "  ${ICON_DB} PostgreSQL: ${CYAN}localhost:5432${NC}"
    echo ""
    echo -e "  Run locally:"
    echo -e "    ${DIM}python -m uvicorn api.main:app --reload --port 8000${NC}"
    echo -e "    ${DIM}python bot/main.py${NC}"
    echo -e "    ${DIM}cd webapp && npm run dev${NC}"
}

stop_dev() {
    log_step "Stopping development environment..."
    docker compose -f "$DEV_COMPOSE" down
    log_ok "Development stopped"
}

stop_all() {
    log_step "Stopping all environments..."
    docker compose -f "$PROD_COMPOSE" down 2>/dev/null || true
    docker compose -f "$DEV_COMPOSE" down 2>/dev/null || true
    log_ok "All environments stopped"
}

switch_env() {
    local target=$1
    local current=$(get_running_env)
    
    if [ "$current" = "$target" ]; then
        log_info "Already running $target"
        return 0
    fi
    
    log_step "Switching to $target environment..."
    
    # Stop current
    if [ "$current" = "prod" ]; then
        stop_prod
    elif [ "$current" = "dev" ]; then
        stop_dev
    elif [ "$current" = "both" ]; then
        stop_all
    fi
    
    # Start target
    if [ "$target" = "prod" ]; then
        start_prod
    elif [ "$target" = "dev" ]; then
        start_dev
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
#  UPDATE & BUILD
# ═══════════════════════════════════════════════════════════════════════════════

update() {
    log_step "Updating TG Player..."
    echo ""
    
    # Check for uncommitted changes
    if has_changes; then
        log_warn "You have uncommitted changes!"
        echo ""
        git status --short
        echo ""
        read -p "Stash changes and continue? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash
            log_ok "Changes stashed"
        else
            log_error "Update cancelled"
            return 1
        fi
    fi
    
    # Pull updates
    log_step "Pulling latest changes..."
    git pull
    
    # Check if prod is running
    local running=$(get_running_env)
    
    if [ "$running" = "prod" ] || [ "$running" = "both" ]; then
        log_step "Rebuilding and restarting production..."
        docker compose -f "$PROD_COMPOSE" up -d --build
        log_ok "Production updated and restarted"
    else
        log_info "Production not running, skipping restart"
        log_info "Run './manage.sh prod start' to start"
    fi
    
    echo ""
    log_ok "Update complete!"
}

rebuild() {
    local service=$1
    
    if [ -z "$service" ]; then
        log_step "Rebuilding all images (no cache)..."
        docker compose -f "$PROD_COMPOSE" build --no-cache
    else
        log_step "Rebuilding $service..."
        docker compose -f "$PROD_COMPOSE" build --no-cache "$service"
    fi
    
    log_ok "Rebuild complete"
}

# ═══════════════════════════════════════════════════════════════════════════════
#  LOGS
# ═══════════════════════════════════════════════════════════════════════════════

show_logs() {
    local env=$1
    local service=$2
    local lines=${3:-100}
    
    local compose_file=""
    if [ "$env" = "prod" ]; then
        compose_file="$PROD_COMPOSE"
    else
        compose_file="$DEV_COMPOSE"
    fi
    
    if [ -z "$service" ]; then
        docker compose -f "$compose_file" logs -f --tail="$lines"
    else
        docker compose -f "$compose_file" logs -f --tail="$lines" "$service"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
#  GIT OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

git_status() {
    echo -e "${BOLD}${ICON_GIT} Git Status${NC}"
    echo ""
    git status
}

git_log() {
    local count=${1:-10}
    echo -e "${BOLD}${ICON_GIT} Recent Commits${NC}"
    echo ""
    git log --oneline --graph --decorate -n "$count"
}

git_branches() {
    echo -e "${BOLD}${ICON_GIT} Branches${NC}"
    echo ""
    git branch -a --color
}

git_checkout() {
    local branch=$1
    
    if [ -z "$branch" ]; then
        log_error "Branch name required"
        return 1
    fi
    
    if has_changes; then
        log_warn "You have uncommitted changes!"
        read -p "Stash and switch? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash
        else
            return 1
        fi
    fi
    
    log_step "Switching to branch: $branch"
    git checkout "$branch"
    
    # Ask about restart
    local running=$(get_running_env)
    if [ "$running" != "none" ]; then
        read -p "Rebuild and restart running services? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            if [ "$running" = "prod" ] || [ "$running" = "both" ]; then
                docker compose -f "$PROD_COMPOSE" up -d --build
            fi
        fi
    fi
}

git_diff() {
    git diff --color
}

# ═══════════════════════════════════════════════════════════════════════════════
#  DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

db_shell() {
    local env=$1
    local container=""
    
    if [ "$env" = "dev" ]; then
        container="tg_player_db_dev"
    else
        container="tg_player_db"
    fi
    
    log_step "Connecting to PostgreSQL ($env)..."
    docker exec -it "$container" psql -U postgres -d tg_player
}

db_backup() {
    local env=$1
    local container=""
    local filename="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if [ "$env" = "dev" ]; then
        container="tg_player_db_dev"
        filename="dev_$filename"
    else
        container="tg_player_db"
        filename="prod_$filename"
    fi
    
    log_step "Creating backup: $filename"
    docker exec "$container" pg_dump -U postgres tg_player > "$filename"
    log_ok "Backup saved: $filename"
}

db_restore() {
    local env=$1
    local filename=$2
    local container=""
    
    if [ -z "$filename" ]; then
        log_error "Backup file required"
        return 1
    fi
    
    if [ ! -f "$filename" ]; then
        log_error "File not found: $filename"
        return 1
    fi
    
    if [ "$env" = "dev" ]; then
        container="tg_player_db_dev"
    else
        container="tg_player_db"
    fi
    
    log_warn "This will OVERWRITE the $env database!"
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    
    log_step "Restoring from: $filename"
    cat "$filename" | docker exec -i "$container" psql -U postgres tg_player
    log_ok "Database restored"
}

# ═══════════════════════════════════════════════════════════════════════════════
#  INTERACTIVE MENU
# ═══════════════════════════════════════════════════════════════════════════════

show_menu() {
    print_header
    
    local running=$(get_running_env)
    local branch=$(get_branch)
    
    echo -e "  ${DIM}Branch: ${NC}${CYAN}$branch${NC}  ${DIM}|  Running: ${NC}${GREEN}$running${NC}"
    echo ""
    echo -e "  ${BOLD}Environment${NC}"
    echo -e "    ${CYAN}1${NC}) Start Production    ${CYAN}2${NC}) Stop Production"
    echo -e "    ${CYAN}3${NC}) Start Development   ${CYAN}4${NC}) Stop Development"
    echo -e "    ${CYAN}5${NC}) Restart Production  ${CYAN}6${NC}) Stop All"
    echo ""
    echo -e "  ${BOLD}Operations${NC}"
    echo -e "    ${CYAN}u${NC}) Update (git pull + rebuild)"
    echo -e "    ${CYAN}r${NC}) Rebuild images"
    echo -e "    ${CYAN}s${NC}) Full status"
    echo -e "    ${CYAN}l${NC}) View logs"
    echo ""
    echo -e "  ${BOLD}Git${NC}"
    echo -e "    ${CYAN}g${NC}) Git status"
    echo -e "    ${CYAN}b${NC}) List branches"
    echo -e "    ${CYAN}c${NC}) Checkout branch"
    echo -e "    ${CYAN}h${NC}) Commit history"
    echo ""
    echo -e "  ${BOLD}Database${NC}"
    echo -e "    ${CYAN}d${NC}) Database shell"
    echo -e "    ${CYAN}B${NC}) Backup database"
    echo -e "    ${CYAN}R${NC}) Restore database"
    echo ""
    echo -e "    ${CYAN}q${NC}) Quit"
    echo ""
}

logs_submenu() {
    echo ""
    echo -e "  ${BOLD}Select service:${NC}"
    echo -e "    ${CYAN}1${NC}) All services"
    echo -e "    ${CYAN}2${NC}) API"
    echo -e "    ${CYAN}3${NC}) Bot"
    echo -e "    ${CYAN}4${NC}) WebApp"
    echo -e "    ${CYAN}5${NC}) PostgreSQL"
    echo -e "    ${CYAN}0${NC}) Back"
    echo ""
    read -p "  Choose: " choice
    
    local env=$(get_running_env)
    [ "$env" = "none" ] && env="prod"
    [ "$env" = "both" ] && env="prod"
    
    case $choice in
        1) show_logs "$env" "" ;;
        2) show_logs "$env" "api" ;;
        3) show_logs "$env" "bot" ;;
        4) show_logs "$env" "webapp" ;;
        5) show_logs "$env" "postgres" ;;
        0) return ;;
    esac
}

db_submenu() {
    local env=$(get_running_env)
    [ "$env" = "none" ] && { log_error "No database running"; return; }
    [ "$env" = "both" ] && env="prod"
    
    db_shell "$env"
}

interactive_menu() {
    while true; do
        show_menu
        read -p "  Choose: " choice
        
        case $choice in
            1) start_prod ;;
            2) stop_prod ;;
            3) start_dev ;;
            4) stop_dev ;;
            5) restart_prod ;;
            6) stop_all ;;
            u) update ;;
            r) rebuild ;;
            s) show_status; read -p "Press Enter to continue..." ;;
            l) logs_submenu ;;
            g) git_status; read -p "Press Enter to continue..." ;;
            b) git_branches; read -p "Press Enter to continue..." ;;
            c) 
                read -p "  Branch name: " branch
                git_checkout "$branch"
                ;;
            h) git_log; read -p "Press Enter to continue..." ;;
            d) db_submenu ;;
            B) 
                local env=$(get_running_env)
                [ "$env" = "both" ] && env="prod"
                db_backup "$env"
                read -p "Press Enter to continue..."
                ;;
            R)
                read -p "  Backup file: " file
                local env=$(get_running_env)
                [ "$env" = "both" ] && env="prod"
                db_restore "$env" "$file"
                read -p "Press Enter to continue..."
                ;;
            q|Q) 
                echo ""
                log_info "Goodbye!"
                exit 0
                ;;
            *)
                log_error "Invalid option"
                sleep 1
                ;;
        esac
    done
}

# ═══════════════════════════════════════════════════════════════════════════════
#  CLI COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

show_help() {
    echo -e "${BOLD}TG Player Manager${NC} - Server management tool"
    echo ""
    echo -e "${BOLD}Usage:${NC}"
    echo "  ./manage.sh                     Interactive menu"
    echo "  ./manage.sh <command> [args]    Run command directly"
    echo ""
    echo -e "${BOLD}Environment Commands:${NC}"
    echo "  prod start              Start production environment"
    echo "  prod stop               Stop production"
    echo "  prod restart            Restart production"
    echo "  prod logs [service]     View production logs"
    echo ""
    echo "  dev start               Start development (DB only)"
    echo "  dev stop                Stop development"
    echo "  dev logs                View development logs"
    echo ""
    echo "  switch <prod|dev>       Switch environment"
    echo "  stop                    Stop all environments"
    echo ""
    echo -e "${BOLD}Update Commands:${NC}"
    echo "  update                  Pull changes and rebuild"
    echo "  rebuild [service]       Rebuild images (no cache)"
    echo ""
    echo -e "${BOLD}Status Commands:${NC}"
    echo "  status                  Full status"
    echo "  quick                   Quick status line"
    echo ""
    echo -e "${BOLD}Git Commands:${NC}"
    echo "  git status              Git status"
    echo "  git log [n]             Show last n commits"
    echo "  git branches            List branches"
    echo "  git checkout <branch>   Switch branch"
    echo "  git diff                Show changes"
    echo ""
    echo -e "${BOLD}Database Commands:${NC}"
    echo "  db shell [prod|dev]     Open psql shell"
    echo "  db backup [prod|dev]    Create backup"
    echo "  db restore <file>       Restore from backup"
    echo ""
    echo -e "${BOLD}Examples:${NC}"
    echo "  ./manage.sh prod start"
    echo "  ./manage.sh prod logs api"
    echo "  ./manage.sh update"
    echo "  ./manage.sh git checkout develop"
    echo "  ./manage.sh db backup prod"
}

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

main() {
    # Check docker
    check_docker || exit 1
    
    # No arguments - interactive mode
    if [ $# -eq 0 ]; then
        interactive_menu
        exit 0
    fi
    
    # Parse CLI commands
    case "$1" in
        # Environment
        prod)
            case "$2" in
                start) start_prod ;;
                stop) stop_prod ;;
                restart) restart_prod ;;
                logs) show_logs "prod" "$3" ;;
                *) log_error "Unknown prod command: $2"; show_help ;;
            esac
            ;;
        dev)
            case "$2" in
                start) start_dev ;;
                stop) stop_dev ;;
                logs) show_logs "dev" "$3" ;;
                *) log_error "Unknown dev command: $2"; show_help ;;
            esac
            ;;
        switch)
            switch_env "$2"
            ;;
        stop)
            stop_all
            ;;
            
        # Update
        update)
            update
            ;;
        rebuild)
            rebuild "$2"
            ;;
            
        # Status
        status)
            show_status
            ;;
        quick)
            show_quick_status
            ;;
            
        # Git
        git)
            case "$2" in
                status) git_status ;;
                log) git_log "$3" ;;
                branches) git_branches ;;
                checkout) git_checkout "$3" ;;
                diff) git_diff ;;
                *) log_error "Unknown git command: $2" ;;
            esac
            ;;
            
        # Database
        db)
            case "$2" in
                shell) db_shell "${3:-prod}" ;;
                backup) db_backup "${3:-prod}" ;;
                restore) db_restore "${3:-prod}" "$4" ;;
                *) log_error "Unknown db command: $2" ;;
            esac
            ;;
            
        # Help
        help|--help|-h)
            show_help
            ;;
            
        *)
            log_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
