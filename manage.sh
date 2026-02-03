#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  TG Player Manager v2.0
# ═══════════════════════════════════════════════════════════════════════════════
#  Универсальный менеджер для управления dev и prod окружениями
#
#  Использование:
#    ./manage.sh                    # Интерактивное меню
#    ./manage.sh <команда> [args]   # CLI режим
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
#  КОНФИГУРАЦИЯ
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
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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
    echo "║                         ${WHITE}${BOLD}Менеджер сервера v2.0${NC}${CYAN}                              ║"
    echo "║                                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_mini_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  ${WHITE}${BOLD}TG Player Менеджер${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"
}

log_info() { echo -e "${BLUE}${ICON_INFO}${NC} $1"; }
log_ok() { echo -e "${GREEN}${ICON_OK}${NC} $1"; }
log_warn() { echo -e "${YELLOW}${ICON_WARN}${NC} $1"; }
log_error() { echo -e "${RED}${ICON_FAIL}${NC} $1"; }
log_step() { echo -e "${PURPLE}→${NC} $1"; }

# Получить текущую git ветку
get_branch() {
    git branch --show-current 2>/dev/null || echo "неизвестно"
}

# Получить короткий hash коммита
get_commit() {
    git rev-parse --short HEAD 2>/dev/null || echo "неизвестно"
}

# Получить время последнего коммита
get_commit_time() {
    git log -1 --format="%cr" 2>/dev/null || echo "неизвестно"
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
                echo -e "${GREEN}● работает (healthy)${NC}"
            elif [ "$health" = "unhealthy" ]; then
                echo -e "${RED}● работает (unhealthy)${NC}"
            else
                echo -e "${GREEN}● работает${NC}"
            fi
            ;;
        exited)
            echo -e "${RED}○ остановлен${NC}"
            ;;
        restarting)
            echo -e "${YELLOW}◐ перезапуск${NC}"
            ;;
        *)
            echo -e "${DIM}○ не создан${NC}"
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
        echo "оба"
    elif $prod_running; then
        echo "prod"
    elif $dev_running; then
        echo "dev"
    else
        echo "нет"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ФУНКЦИИ СТАТУСА
# ═══════════════════════════════════════════════════════════════════════════════

show_status() {
    print_mini_header
    
    # Git инфо
    echo -e "${BOLD}${ICON_GIT} Git Статус${NC}"
    echo -e "  Ветка:   ${CYAN}$(get_branch)${NC}"
    echo -e "  Коммит:  ${DIM}$(get_commit)${NC} ($(get_commit_time))"
    
    if has_changes; then
        echo -e "  Изменения: ${YELLOW}есть несохранённые${NC}"
    else
        echo -e "  Изменения: ${GREEN}чисто${NC}"
    fi
    
    if has_updates 2>/dev/null; then
        echo -e "  Remote:  ${YELLOW}есть обновления${NC}"
    else
        echo -e "  Remote:  ${GREEN}актуально${NC}"
    fi
    
    echo ""
    
    # Docker статус
    echo -e "${BOLD}${ICON_DOCKER} Docker Сервисы${NC}"
    
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
    
    # Ресурсы
    echo -e "${BOLD}📊 Использование ресурсов${NC}"
    docker stats --no-stream --format "  {{.Name}}: CPU {{.CPUPerc}}, Память {{.MemUsage}}" 2>/dev/null | head -5 || echo "  Нет запущенных контейнеров"
    
    echo ""
}

show_quick_status() {
    local running=$(get_running_env)
    local branch=$(get_branch)
    
    echo -e "${CYAN}TG Player${NC} | Ветка: ${CYAN}$branch${NC} | Запущено: ${GREEN}$running${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
#  УПРАВЛЕНИЕ ОКРУЖЕНИЯМИ
# ═══════════════════════════════════════════════════════════════════════════════

start_prod() {
    log_step "Запуск production окружения..."
    
    # Проверка .env
    if [ ! -f ".env" ]; then
        log_error "Файл .env не найден! Скопируй из .env.example"
        return 1
    fi
    
    docker compose -f "$PROD_COMPOSE" up -d --build
    
    echo ""
    log_ok "Production запущен!"
    echo ""
    echo -e "  ${ICON_API} API:    ${CYAN}http://localhost:${API_PORT:-8000}${NC}"
    echo -e "  ${ICON_WEB} WebApp: ${CYAN}http://localhost:${WEBAPP_PORT:-5173}${NC}"
}

stop_prod() {
    log_step "Остановка production окружения..."
    docker compose -f "$PROD_COMPOSE" down
    log_ok "Production остановлен"
}

restart_prod() {
    log_step "Перезапуск production окружения..."
    docker compose -f "$PROD_COMPOSE" restart
    log_ok "Production перезапущен"
}

start_dev() {
    log_step "Запуск development окружения (только PostgreSQL)..."
    docker compose -f "$DEV_COMPOSE" up -d
    
    echo ""
    log_ok "База данных для разработки запущена!"
    echo ""
    echo -e "  ${ICON_DB} PostgreSQL: ${CYAN}localhost:5432${NC}"
    echo ""
    echo -e "  Запусти локально:"
    echo -e "    ${DIM}python -m uvicorn api.main:app --reload --port 8000${NC}"
    echo -e "    ${DIM}python bot/main.py${NC}"
    echo -e "    ${DIM}cd webapp && npm run dev${NC}"
}

stop_dev() {
    log_step "Остановка development окружения..."
    docker compose -f "$DEV_COMPOSE" down
    log_ok "Development остановлен"
}

stop_all() {
    log_step "Остановка всех окружений..."
    docker compose -f "$PROD_COMPOSE" down 2>/dev/null || true
    docker compose -f "$DEV_COMPOSE" down 2>/dev/null || true
    log_ok "Все окружения остановлены"
}

switch_env() {
    local target=$1
    local current=$(get_running_env)
    
    if [ "$current" = "$target" ]; then
        log_info "Уже запущено $target"
        return 0
    fi
    
    log_step "Переключение на $target окружение..."
    
    # Остановить текущее
    if [ "$current" = "prod" ]; then
        stop_prod
    elif [ "$current" = "dev" ]; then
        stop_dev
    elif [ "$current" = "оба" ]; then
        stop_all
    fi
    
    # Запустить целевое
    if [ "$target" = "prod" ]; then
        start_prod
    elif [ "$target" = "dev" ]; then
        start_dev
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ОБНОВЛЕНИЕ И СБОРКА
# ═══════════════════════════════════════════════════════════════════════════════

update() {
    log_step "Обновление TG Player..."
    echo ""
    
    # Проверка несохранённых изменений
    if has_changes; then
        log_warn "Есть несохранённые изменения!"
        echo ""
        git status --short
        echo ""
        read -p "Сохранить в stash и продолжить? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash
            log_ok "Изменения сохранены в stash"
        else
            log_error "Обновление отменено"
            return 1
        fi
    fi
    
    # Получить обновления
    log_step "Получение последних изменений..."
    git pull
    
    # Проверить запущен ли prod
    local running=$(get_running_env)
    
    if [ "$running" = "prod" ] || [ "$running" = "оба" ]; then
        log_step "Пересборка и перезапуск production..."
        docker compose -f "$PROD_COMPOSE" up -d --build
        log_ok "Production обновлён и перезапущен"
    else
        log_info "Production не запущен, пропускаем перезапуск"
        log_info "Запусти: './manage.sh prod start'"
    fi
    
    echo ""
    log_ok "Обновление завершено!"
}

rebuild() {
    local service=$1
    
    if [ -z "$service" ]; then
        log_step "Пересборка всех образов (без кэша)..."
        docker compose -f "$PROD_COMPOSE" build --no-cache
    else
        log_step "Пересборка $service..."
        docker compose -f "$PROD_COMPOSE" build --no-cache "$service"
    fi
    
    log_ok "Пересборка завершена"
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ЛОГИ
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
#  GIT ОПЕРАЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

git_status() {
    echo -e "${BOLD}${ICON_GIT} Git Статус${NC}"
    echo ""
    git status
}

git_log() {
    local count=${1:-10}
    echo -e "${BOLD}${ICON_GIT} Последние коммиты${NC}"
    echo ""
    git log --oneline --graph --decorate -n "$count"
}

git_branches() {
    echo -e "${BOLD}${ICON_GIT} Ветки${NC}"
    echo ""
    git branch -a --color
}

git_checkout() {
    local branch=$1
    
    if [ -z "$branch" ]; then
        log_error "Нужно указать имя ветки"
        return 1
    fi
    
    if has_changes; then
        log_warn "Есть несохранённые изменения!"
        read -p "Сохранить в stash и переключиться? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash
        else
            return 1
        fi
    fi
    
    log_step "Переключение на ветку: $branch"
    git checkout "$branch"
    
    # Спросить о перезапуске
    local running=$(get_running_env)
    if [ "$running" != "нет" ]; then
        read -p "Пересобрать и перезапустить сервисы? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            if [ "$running" = "prod" ] || [ "$running" = "оба" ]; then
                docker compose -f "$PROD_COMPOSE" up -d --build
            fi
        fi
    fi
}

git_diff() {
    git diff --color
}

# ═══════════════════════════════════════════════════════════════════════════════
#  МИГРАЦИЯ С SYSTEMD
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEMD_SERVICES="tg-player-api tg-player-bot tg-player-webapp"

# Проверить статус systemd сервисов
check_systemd() {
    echo -e "${BOLD}🔧 Статус systemd сервисов${NC}"
    echo ""
    
    for service in $SYSTEMD_SERVICES; do
        local status=$(systemctl is-active "$service" 2>/dev/null || echo "не найден")
        local enabled=$(systemctl is-enabled "$service" 2>/dev/null || echo "—")
        
        case "$status" in
            active)
                echo -e "  ${GREEN}●${NC} $service: ${GREEN}работает${NC} (автозапуск: $enabled)"
                ;;
            inactive)
                echo -e "  ${RED}○${NC} $service: ${DIM}остановлен${NC} (автозапуск: $enabled)"
                ;;
            *)
                echo -e "  ${DIM}○${NC} $service: ${DIM}$status${NC}"
                ;;
        esac
    done
    echo ""
}

# Остановить и отключить systemd сервисы
stop_systemd() {
    log_step "Остановка systemd сервисов..."
    
    for service in $SYSTEMD_SERVICES; do
        if systemctl is-active "$service" &>/dev/null; then
            sudo systemctl stop "$service"
            log_ok "Остановлен: $service"
        fi
    done
}

disable_systemd() {
    log_step "Отключение автозапуска systemd сервисов..."
    
    for service in $SYSTEMD_SERVICES; do
        if systemctl is-enabled "$service" &>/dev/null; then
            sudo systemctl disable "$service"
            log_ok "Отключён: $service"
        fi
    done
}

# Бэкап базы из systemd (PostgreSQL или SQLite)
backup_host_db() {
    local filename="migration_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log_step "Создание бэкапа базы данных хоста..."
    
    # Определяем тип базы данных из .env
    local db_url=""
    if [ -f ".env" ]; then
        db_url=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
    fi
    
    # Проверяем SQLite
    if [[ "$db_url" == *"sqlite"* ]] || [ -f "tg_player.db" ]; then
        log_info "Обнаружена SQLite база данных"
        
        if [ -f "tg_player.db" ]; then
            local sqlite_backup="migration_backup_$(date +%Y%m%d_%H%M%S).db"
            cp tg_player.db "$sqlite_backup"
            log_ok "SQLite бэкап сохранён: $sqlite_backup"
            echo "$sqlite_backup"
            return 0
        else
            log_error "SQLite файл tg_player.db не найден"
            return 1
        fi
    fi
    
    # PostgreSQL на хосте
    if command -v pg_dump &>/dev/null; then
        sudo -u postgres pg_dump tg_player > "$filename"
        log_ok "PostgreSQL бэкап сохранён: $filename"
        echo "$filename"
    else
        log_error "pg_dump не найден. Установи PostgreSQL client или сделай бэкап вручную"
        return 1
    fi
}

# Миграция данных из SQLite в Docker PostgreSQL
migrate_sqlite_data() {
    log_step "Миграция данных из SQLite в PostgreSQL..."
    
    if [ ! -f "tg_player.db" ]; then
        log_error "SQLite файл tg_player.db не найден"
        return 1
    fi
    
    # Проверяем что PostgreSQL контейнер работает
    if ! docker exec tg_player_db pg_isready -U postgres &>/dev/null; then
        log_error "PostgreSQL контейнер не готов. Запустите: docker compose -f docker-compose.prod.yml up -d"
        return 1
    fi
    
    # Запускаем Python скрипт миграции
    if [ -f "scripts/migrate_sqlite_to_postgres.py" ]; then
        python3 scripts/migrate_sqlite_to_postgres.py --sqlite tg_player.db --docker
        return $?
    else
        log_error "Скрипт миграции не найден: scripts/migrate_sqlite_to_postgres.py"
        return 1
    fi
}

# Полная миграция с systemd на Docker
migrate_to_docker() {
    print_mini_header
    echo -e "${BOLD}${ICON_ROCKET} Миграция с systemd на Docker${NC}"
    echo ""
    
    # Показать текущий статус
    check_systemd
    
    echo -e "${YELLOW}Это выполнит:${NC}"
    echo "  1. Создаст бэкап базы данных"
    echo "  2. Остановит systemd сервисы (api, bot, webapp)"
    echo "  3. Отключит их автозапуск"
    echo "  4. Запустит Docker контейнеры"
    echo "  5. Восстановит базу в Docker PostgreSQL"
    echo ""
    
    read -p "Продолжить миграцию? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Миграция отменена"
        return 0
    fi
    
    echo ""
    
    # Шаг 1: Бэкап
    log_step "Шаг 1/5: Бэкап базы данных..."
    local backup_file=$(backup_host_db)
    if [ $? -ne 0 ]; then
        log_error "Не удалось создать бэкап. Миграция прервана."
        return 1
    fi
    
    # Шаг 2: Остановка systemd
    echo ""
    log_step "Шаг 2/5: Остановка systemd сервисов..."
    stop_systemd
    
    # Шаг 3: Отключение автозапуска
    echo ""
    log_step "Шаг 3/5: Отключение автозапуска..."
    disable_systemd
    
    # Шаг 4: Запуск Docker
    echo ""
    log_step "Шаг 4/5: Запуск Docker контейнеров..."
    
    if [ ! -f ".env" ]; then
        log_warn "Файл .env не найден, копирую из .env.example"
        cp .env.example .env
        log_warn "Отредактируй .env и запусти миграцию заново!"
        return 1
    fi
    
    docker compose -f "$PROD_COMPOSE" up -d --build
    
    # Подождать пока PostgreSQL поднимется
    log_step "Ожидание запуска PostgreSQL..."
    sleep 10
    
    # Шаг 5: Восстановление базы
    echo ""
    log_step "Шаг 5/5: Восстановление базы данных..."
    
    if [ -f "$backup_file" ]; then
        # Проверяем тип бэкапа (SQLite .db или PostgreSQL .sql)
        if [[ "$backup_file" == *.db ]]; then
            log_info "Обнаружен SQLite бэкап, запускаю миграцию данных..."
            migrate_sqlite_data
        else
            # PostgreSQL SQL дамп
            cat "$backup_file" | docker exec -i tg_player_db psql -U postgres -d tg_player
        fi
        log_ok "База данных восстановлена"
    else
        log_warn "Файл бэкапа не найден, пропускаю восстановление"
        
        # Проверяем есть ли SQLite база для миграции
        if [ -f "tg_player.db" ]; then
            log_info "Найден файл tg_player.db, запускаю миграцию..."
            migrate_sqlite_data
        fi
    fi
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    log_ok "Миграция завершена!"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Бэкап сохранён: $backup_file"
    echo ""
    echo "  Проверь статус: ./manage.sh status"
    echo "  Логи:           ./manage.sh prod logs"
    echo ""
    echo -e "  ${DIM}Старые systemd сервисы отключены, но файлы остались в /etc/systemd/system/${NC}"
    echo -e "  ${DIM}Удалить их можно командой: sudo rm /etc/systemd/system/tg-player-*.service${NC}"
}

# Откат на systemd (если что-то пошло не так)
rollback_to_systemd() {
    print_mini_header
    echo -e "${BOLD}⏪ Откат на systemd${NC}"
    echo ""
    
    log_warn "Это остановит Docker и вернёт systemd сервисы"
    read -p "Продолжить? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 0
    fi
    
    # Остановить Docker
    log_step "Остановка Docker контейнеров..."
    docker compose -f "$PROD_COMPOSE" down
    
    # Включить и запустить systemd
    log_step "Включение systemd сервисов..."
    for service in $SYSTEMD_SERVICES; do
        sudo systemctl enable "$service" 2>/dev/null || true
        sudo systemctl start "$service" 2>/dev/null || true
    done
    
    log_ok "Откат завершён"
    check_systemd
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ОПЕРАЦИИ С БАЗОЙ ДАННЫХ
# ═══════════════════════════════════════════════════════════════════════════════

db_shell() {
    local env=$1
    local container=""
    
    if [ "$env" = "dev" ]; then
        container="tg_player_db_dev"
    else
        container="tg_player_db"
    fi
    
    log_step "Подключение к PostgreSQL ($env)..."
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
    
    log_step "Создание бэкапа: $filename"
    docker exec "$container" pg_dump -U postgres tg_player > "$filename"
    log_ok "Бэкап сохранён: $filename"
}

db_restore() {
    local env=$1
    local filename=$2
    local container=""
    
    if [ -z "$filename" ]; then
        log_error "Нужно указать файл бэкапа"
        return 1
    fi
    
    if [ ! -f "$filename" ]; then
        log_error "Файл не найден: $filename"
        return 1
    fi
    
    if [ "$env" = "dev" ]; then
        container="tg_player_db_dev"
    else
        container="tg_player_db"
    fi
    
    log_warn "Это ПЕРЕЗАПИШЕТ базу данных $env!"
    read -p "Продолжить? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    
    log_step "Восстановление из: $filename"
    cat "$filename" | docker exec -i "$container" psql -U postgres tg_player
    log_ok "База данных восстановлена"
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ИНТЕРАКТИВНОЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════════════════════

show_menu() {
    print_header
    
    local running=$(get_running_env)
    local branch=$(get_branch)
    
    echo -e "  ${DIM}Ветка: ${NC}${CYAN}$branch${NC}  ${DIM}|  Запущено: ${NC}${GREEN}$running${NC}"
    echo ""
    echo -e "  ${BOLD}Окружение${NC}"
    echo -e "    ${CYAN}1${NC}) Запустить Production    ${CYAN}2${NC}) Остановить Production"
    echo -e "    ${CYAN}3${NC}) Запустить Development   ${CYAN}4${NC}) Остановить Development"
    echo -e "    ${CYAN}5${NC}) Перезапустить Prod      ${CYAN}6${NC}) Остановить всё"
    echo ""
    echo -e "  ${BOLD}Операции${NC}"
    echo -e "    ${CYAN}u${NC}) Обновить (git pull + пересборка)"
    echo -e "    ${CYAN}r${NC}) Пересобрать образы"
    echo -e "    ${CYAN}s${NC}) Полный статус"
    echo -e "    ${CYAN}l${NC}) Просмотр логов"
    echo ""
    echo -e "  ${BOLD}Git${NC}"
    echo -e "    ${CYAN}g${NC}) Git статус"
    echo -e "    ${CYAN}b${NC}) Список веток"
    echo -e "    ${CYAN}c${NC}) Переключить ветку"
    echo -e "    ${CYAN}h${NC}) История коммитов"
    echo ""
    echo -e "  ${BOLD}База данных${NC}"
    echo -e "    ${CYAN}d${NC}) Консоль БД"
    echo -e "    ${CYAN}B${NC}) Бэкап базы"
    echo -e "    ${CYAN}R${NC}) Восстановить базу"
    echo ""
    echo -e "  ${BOLD}Миграция${NC}"
    echo -e "    ${CYAN}m${NC}) Мигрировать с systemd на Docker"
    echo -e "    ${CYAN}M${NC}) Откат на systemd"
    echo -e "    ${CYAN}S${NC}) Статус systemd сервисов"
    echo ""
    echo -e "    ${CYAN}q${NC}) Выход"
    echo ""
}

logs_submenu() {
    echo ""
    echo -e "  ${BOLD}Выбери сервис:${NC}"
    echo -e "    ${CYAN}1${NC}) Все сервисы"
    echo -e "    ${CYAN}2${NC}) API"
    echo -e "    ${CYAN}3${NC}) Бот"
    echo -e "    ${CYAN}4${NC}) WebApp"
    echo -e "    ${CYAN}5${NC}) PostgreSQL"
    echo -e "    ${CYAN}0${NC}) Назад"
    echo ""
    read -p "  Выбор: " choice
    
    local env=$(get_running_env)
    [ "$env" = "нет" ] && env="prod"
    [ "$env" = "оба" ] && env="prod"
    
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
    [ "$env" = "нет" ] && { log_error "База данных не запущена"; return; }
    [ "$env" = "оба" ] && env="prod"
    
    db_shell "$env"
}

interactive_menu() {
    while true; do
        show_menu
        read -p "  Выбор: " choice
        
        case $choice in
            1) start_prod ;;
            2) stop_prod ;;
            3) start_dev ;;
            4) stop_dev ;;
            5) restart_prod ;;
            6) stop_all ;;
            u) update ;;
            r) rebuild ;;
            s) show_status; read -p "Нажми Enter для продолжения..." ;;
            l) logs_submenu ;;
            g) git_status; read -p "Нажми Enter для продолжения..." ;;
            b) git_branches; read -p "Нажми Enter для продолжения..." ;;
            c) 
                read -p "  Имя ветки: " branch
                git_checkout "$branch"
                ;;
            h) git_log; read -p "Нажми Enter для продолжения..." ;;
            d) db_submenu ;;
            B) 
                local env=$(get_running_env)
                [ "$env" = "оба" ] && env="prod"
                db_backup "$env"
                read -p "Нажми Enter для продолжения..."
                ;;
            R)
                read -p "  Файл бэкапа: " file
                local env=$(get_running_env)
                [ "$env" = "оба" ] && env="prod"
                db_restore "$env" "$file"
                read -p "Нажми Enter для продолжения..."
                ;;
            m) migrate_to_docker; read -p "Нажми Enter для продолжения..." ;;
            M) rollback_to_systemd; read -p "Нажми Enter для продолжения..." ;;
            S) check_systemd; read -p "Нажми Enter для продолжения..." ;;
            q|Q) 
                echo ""
                log_info "Пока!"
                exit 0
                ;;
            *)
                log_error "Неверный выбор"
                sleep 1
                ;;
        esac
    done
}

# ═══════════════════════════════════════════════════════════════════════════════
#  CLI КОМАНДЫ
# ═══════════════════════════════════════════════════════════════════════════════

show_help() {
    echo -e "${BOLD}TG Player Менеджер${NC} - Управление сервером"
    echo ""
    echo -e "${BOLD}Использование:${NC}"
    echo "  ./manage.sh                     Интерактивное меню"
    echo "  ./manage.sh <команда> [аргументы]    Выполнить команду"
    echo ""
    echo -e "${BOLD}Команды окружения:${NC}"
    echo "  prod start              Запустить production"
    echo "  prod stop               Остановить production"
    echo "  prod restart            Перезапустить production"
    echo "  prod logs [сервис]      Логи production"
    echo ""
    echo "  dev start               Запустить development (только БД)"
    echo "  dev stop                Остановить development"
    echo "  dev logs                Логи development"
    echo ""
    echo "  switch <prod|dev>       Переключить окружение"
    echo "  stop                    Остановить всё"
    echo ""
    echo -e "${BOLD}Команды обновления:${NC}"
    echo "  update                  Получить изменения и пересобрать"
    echo "  rebuild [сервис]        Пересобрать образы (без кэша)"
    echo ""
    echo -e "${BOLD}Команды статуса:${NC}"
    echo "  status                  Полный статус"
    echo "  quick                   Краткий статус"
    echo ""
    echo -e "${BOLD}Git команды:${NC}"
    echo "  git status              Git статус"
    echo "  git log [n]             Последние n коммитов"
    echo "  git branches            Список веток"
    echo "  git checkout <ветка>    Переключить ветку"
    echo "  git diff                Показать изменения"
    echo ""
    echo -e "${BOLD}Команды БД:${NC}"
    echo "  db shell [prod|dev]     Открыть psql консоль"
    echo "  db backup [prod|dev]    Создать бэкап"
    echo "  db restore <файл>       Восстановить из бэкапа"
    echo "  db migrate-sqlite       Мигрировать данные из SQLite в Docker PostgreSQL"
    echo ""
    echo -e "${BOLD}Миграция:${NC}"
    echo "  migrate                 Мигрировать с systemd на Docker"
    echo "  migrate-data            Только миграция данных SQLite → PostgreSQL"
    echo "  rollback                Откатиться на systemd"
    echo "  systemd status          Статус systemd сервисов"
    echo "  systemd stop            Остановить systemd сервисы"
    echo "  systemd disable         Отключить автозапуск systemd"
    echo ""
    echo -e "${BOLD}Примеры:${NC}"
    echo "  ./manage.sh prod start"
    echo "  ./manage.sh prod logs api"
    echo "  ./manage.sh update"
    echo "  ./manage.sh git checkout develop"
    echo "  ./manage.sh db backup prod"
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

main() {
    # Проверка docker
    check_docker || exit 1
    
    # Без аргументов - интерактивный режим
    if [ $# -eq 0 ]; then
        interactive_menu
        exit 0
    fi
    
    # Разбор CLI команд
    case "$1" in
        # Окружение
        prod)
            case "$2" in
                start) start_prod ;;
                stop) stop_prod ;;
                restart) restart_prod ;;
                logs) show_logs "prod" "$3" ;;
                *) log_error "Неизвестная команда prod: $2"; show_help ;;
            esac
            ;;
        dev)
            case "$2" in
                start) start_dev ;;
                stop) stop_dev ;;
                logs) show_logs "dev" "$3" ;;
                *) log_error "Неизвестная команда dev: $2"; show_help ;;
            esac
            ;;
        switch)
            switch_env "$2"
            ;;
        stop)
            stop_all
            ;;
            
        # Обновление
        update)
            update
            ;;
        rebuild)
            rebuild "$2"
            ;;
            
        # Статус
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
                *) log_error "Неизвестная git команда: $2" ;;
            esac
            ;;
            
        # База данных
        db)
            case "$2" in
                shell) db_shell "${3:-prod}" ;;
                backup) db_backup "${3:-prod}" ;;
                restore) db_restore "${3:-prod}" "$4" ;;
                migrate-sqlite) migrate_sqlite_data ;;
                *) log_error "Неизвестная db команда: $2"; echo "Доступно: shell, backup, restore, migrate-sqlite" ;;
            esac
            ;;
        
        # Миграция с systemd
        migrate)
            migrate_to_docker
            ;;
        migrate-data)
            # Только миграция данных из SQLite (без остановки systemd)
            migrate_sqlite_data
            ;;
        rollback)
            rollback_to_systemd
            ;;
        systemd)
            case "$2" in
                status) check_systemd ;;
                stop) stop_systemd ;;
                disable) disable_systemd ;;
                *) log_error "Неизвестная systemd команда: $2"; echo "Доступно: status, stop, disable" ;;
            esac
            ;;
            
        # Помощь
        help|--help|-h)
            show_help
            ;;
            
        *)
            log_error "Неизвестная команда: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
