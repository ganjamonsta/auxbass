@echo off
chcp 65001 >nul
title TG Player - Local Dev Launcher
echo ====================================================
echo        🎵 TG Player - Local Development Launcher
echo ====================================================
echo.

REM Проверяем есть ли .env.local
if not exist ".env.local" (
    echo [ERROR] Файл .env.local не найден!
    echo.
    echo Создай его:
    echo   copy .env.example .env.local
    echo.
    echo И заполни данными для локальной разработки.
    echo См. docs\local_development.md
    pause
    exit /b 1
)

REM Копируем .env.local в .env для запуска
copy /Y .env.local .env >nul

echo [OK] Используем .env.local (скопирован в .env)
echo.
echo Что запустить?
echo.
echo   1. API (FastAPI backend на http://localhost:8000)
echo   2. Bot (Telegram bot)  
echo   3. Webapp Dev (Vite dev-сервер: http://localhost:5173/?dev=1)
echo   4. Все вместе (API + Bot + Vite Dev в 3 окнах)
echo   5. 📦 Собрать Webapp (npm run build -> webapp\dist)
echo   6. 🚀 Собрать Webapp и запустить всё (Build -> API + Bot + Webapp)
echo   7. PostgreSQL (Docker)
echo.
set /p choice="Выбери (1-7): "

if "%choice%"=="1" (
    echo.
    echo Запускаю API на http://localhost:8000
    echo Ctrl+C для остановки
    echo.
    python -m uvicorn api.main:app --reload --port 8000
)

if "%choice%"=="2" (
    echo.
    echo Запускаю Telegram Bot
    echo Ctrl+C для остановки
    echo.
    python bot/main.py
)

if "%choice%"=="3" (
    echo.
    echo Запускаю Webapp Dev на http://localhost:5173
    echo Открой в браузере: http://localhost:5173/?dev=1
    echo Ctrl+C для остановки
    echo.
    cd /d "%~dp0webapp"
    call npm run dev
)

if "%choice%"=="4" (
    echo.
    echo Запускаю всё в отдельных окнах...
    start "TG Player API (:8000)" cmd /k "python -m uvicorn api.main:app --reload --port 8000"
    start "TG Player Bot" cmd /k "python bot/main.py"
    start "TG Player Webapp Dev (:5173)" cmd /k "cd /d \"%~dp0webapp\" && npm run dev"
    echo.
    echo [OK] Открыто 3 окна:
    echo   - API:        http://localhost:8000
    echo   - Webapp Dev: http://localhost:5173/?dev=1 (горячая перезагрузка Vite)
    echo.
    pause
)

if "%choice%"=="5" (
    echo.
    echo ====================================================
    echo   📦 Сборка Webapp (npm run build)
    echo ====================================================
    cd /d "%~dp0webapp"
    call npm run build
    echo.
    if %ERRORLEVEL% equ 0 (
        echo [OK] Сборка успешно завершена! Обновлен webapp\dist\
        echo Теперь FastAPI на http://localhost:8000 и бот отдают свежую версию.
    ) else (
        echo [ERROR] Ошибка при сборке Webapp!
    )
    echo.
    pause
)

if "%choice%"=="6" (
    echo.
    echo ====================================================
    echo   Шаг 1: 📦 Сборка свежего Webapp...
    echo ====================================================
    cd /d "%~dp0webapp"
    call npm run build
    cd /d "%~dp0"
    echo.
    echo ====================================================
    echo   Шаг 2: 🚀 Запуск сервисов в 3 окнах...
    echo ====================================================
    start "TG Player API (:8000)" cmd /k "python -m uvicorn api.main:app --reload --port 8000"
    start "TG Player Bot" cmd /k "python bot/main.py"
    start "TG Player Webapp Dev (:5173)" cmd /k "cd /d \"%~dp0webapp\" && npm run dev"
    echo.
    echo [OK] Всё запущено со свежесобранным dist!
    echo   - FastAPI + Dist (для Telegram): http://localhost:8000/?dev=1
    echo   - Vite Dev (для живой правки UI): http://localhost:5173/?dev=1
    echo.
    pause
)

if "%choice%"=="7" (
    echo.
    echo Запускаю PostgreSQL в Docker...
    docker-compose up -d postgres
    echo.
    echo База запущена на localhost:5432
    echo.
    pause
)

