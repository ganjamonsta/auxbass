#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  TG Player Manager v2.0
# ═══════════════════════════════════════════════════════════════════════════════
#  Менеджер для управления production окружением
#
#  Использование:
#    ./manage.sh                    # Интерактивное меню
#    ./manage.sh <команда> [args]   # CLI режим
#
#  Примеры:
#    ./manage.sh status             # Статус всех сервисов
#    ./manage.sh start              # Запустить production
#    ./manage.sh logs api           # Логи API
#    ./manage.sh update             # Обновить код и пересобрать
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# ═══════════════════════════════════════════════════════════════════════════════
#  КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Файлы конфигурации
PROD_COMPOSE="docker-compose.prod.yml"
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

# Проверить запущено ли prod окружение
get_running_env() {
    if docker compose -f "$PROD_COMPOSE" ps -q 2>/dev/null | grep -q .; then
        echo "prod"
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
    
    if [ "$running" = "prod" ]; then
        log_step "Пересборка и перезапуск production..."
        docker compose -f "$PROD_COMPOSE" up -d --build
        log_ok "Production обновлён и перезапущен"
    else
        log_info "Production не запущен, пропускаем перезапуск"
        log_info "Запусти: './manage.sh start'"
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
    local service=$1
    local lines=${2:-100}
    
    if [ -z "$service" ]; then
        docker compose -f "$PROD_COMPOSE" logs -f --tail="$lines"
    else
        docker compose -f "$PROD_COMPOSE" logs -f --tail="$lines" "$service"
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
            docker compose -f "$PROD_COMPOSE" up -d --build
        fi
    fi
}

git_diff() {
    git diff --color
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ОПЕРАЦИИ С БАЗОЙ ДАННЫХ
# ═══════════════════════════════════════════════════════════════════════════════

db_shell() {
    log_step "Подключение к PostgreSQL..."
    docker exec -it tg_player_db psql -U postgres -d tg_player
}

db_backup() {
    local filename="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log_step "Создание бэкапа: $filename"
    docker exec tg_player_db pg_dump -U postgres tg_player > "$filename"
    log_ok "Бэкап сохранён: $filename"
}

db_restore() {
    local filename=$1
    
    if [ -z "$filename" ]; then
        log_error "Нужно указать файл бэкапа"
        return 1
    fi
    
    if [ ! -f "$filename" ]; then
        log_error "Файл не найден: $filename"
        return 1
    fi
    
    log_warn "Это ПЕРЕЗАПИШЕТ базу данных!"
    read -p "Продолжить? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    
    log_step "Восстановление из: $filename"
    cat "$filename" | docker exec -i tg_player_db psql -U postgres tg_player
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
    echo -e "    ${CYAN}3${NC}) Перезапустить Prod"
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
    
    case $choice in
        1) show_logs "" ;;
        2) show_logs "api" ;;
        3) show_logs "bot" ;;
        4) show_logs "webapp" ;;
        5) show_logs "postgres" ;;
        0|"") return ;;
        *) log_error "Неверный выбор"; sleep 1 ;;
    esac
}

db_submenu() {
    local running=$(get_running_env)
    [ "$running" = "нет" ] && { log_error "База данных не запущена"; return; }
    
    db_shell
}

interactive_menu() {
    while true; do
        show_menu
        read -p "  Выбор: " choice
        
        case $choice in
            1) start_prod ;;
            2) stop_prod ;;
            3) restart_prod ;;
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
                db_backup
                read -p "Нажми Enter для продолжения..."
                ;;
            R)
                read -p "  Файл бэкапа: " file
                db_restore "$file"
                read -p "Нажми Enter для продолжения..."
                ;;
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
    echo "  start                   Запустить production"
    echo "  stop                    Остановить production"
    echo "  restart                 Перезапустить production"
    echo "  logs [сервис]           Логи production"
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
    echo "  db shell                Открыть psql консоль"
    echo "  db backup               Создать бэкап"
    echo "  db restore <файл>       Восстановить из бэкапа"
    echo ""
    echo -e "${BOLD}Примеры:${NC}"
    echo "  ./manage.sh start"
    echo "  ./manage.sh logs api"
    echo "  ./manage.sh update"
    echo "  ./manage.sh git checkout develop"
    echo "  ./manage.sh db backup"
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
        start)
            start_prod
            ;;
        stop)
            stop_prod
            ;;
        restart)
            restart_prod
            ;;
        logs)
            show_logs "$2"
            ;;
        # Обратная совместимость с prod командами
        prod)
            case "$2" in
                start) start_prod ;;
                stop) stop_prod ;;
                restart) restart_prod ;;
                logs) show_logs "$3" ;;
                *) log_error "Неизвестная команда: $2"; show_help ;;
            esac
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
                shell) db_shell ;;
                backup) db_backup ;;
                restore) db_restore "$3" ;;
                *) log_error "Неизвестная db команда: $2"; echo "Доступно: shell, backup, restore" ;;
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
