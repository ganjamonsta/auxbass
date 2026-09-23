@echo off
chcp 65001 >nul
title TG Player - Сборка Webapp
echo ====================================================
echo        📦 TG Player - Сборка Webapp (Production)
echo ====================================================
echo.
cd /d "%~dp0webapp"

echo Запускаю Vite build...
call npm run build

echo.
if %ERRORLEVEL% equ 0 (
    echo ====================================================
    echo [OK] Сборка успешно завершена! Файлы в webapp\dist\
    echo.
    echo Теперь FastAPI на http://localhost:8000 (и бот в Telegram)
    echo будут отдавать самую свежую версию интерфейса.
    echo ====================================================
) else (
    echo ====================================================
    echo [ERROR] Во время сборки произошла ошибка!
    echo ====================================================
)
echo.
pause
