@echo off
chcp 65001 > nul
setlocal

echo ========================================================
echo        🚀 TG Player - WebApp Release Publisher
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] 🔨 Сборка WebApp (Vite)...
cd webapp
call npm run build
if %errorlevel% neq 0 (
    echo.
    echo ❌ Ошибка при сборке WebApp!
    cd ..
    pause
    exit /b %errorlevel%
)
cd ..

echo.
echo [2/3] 📦 Упаковка и публикация релиза на GitHub...
python scripts\publish_release.py
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ Публикация завершилась с ошибкой.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] 💾 Очистка временных архивов...
if exist webapp-dist.tar.gz del webapp-dist.tar.gz

echo.
echo ========================================================
echo   ✅ Всё готово! Теперь перезапустите бота в Pterodactyl.
echo ========================================================
echo.
pause
