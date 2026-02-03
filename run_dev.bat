@echo off
echo ========================================
echo    TG Player - Local Development
echo ========================================
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

echo [OK] Используем .env.local
echo.
echo Что запустить?
echo.
echo   1. API (FastAPI backend)
echo   2. Bot (Telegram bot)  
echo   3. Webapp (Vue.js frontend)
echo   4. Все вместе (3 окна)
echo   5. PostgreSQL (Docker)
echo.
set /p choice="Выбери (1-5): "

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
    echo Запускаю Webapp на http://localhost:5173
    echo Ctrl+C для остановки
    echo.
    cd webapp
    npm run dev
)

if "%choice%"=="4" (
    echo.
    echo Запускаю всё в отдельных окнах...
    start "TG Player API" cmd /k "python -m uvicorn api.main:app --reload --port 8000"
    start "TG Player Bot" cmd /k "python bot/main.py"
    start "TG Player Webapp" cmd /k "cd webapp && npm run dev"
    echo.
    echo Готово! Открыто 3 окна.
    echo.
    pause
)

if "%choice%"=="5" (
    echo.
    echo Запускаю PostgreSQL в Docker...
    docker-compose up -d postgres
    echo.
    echo База запущена на localhost:5432
    echo.
    pause
)
