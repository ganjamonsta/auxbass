@echo off
setlocal

echo ========================================================
echo        TG Player - WebApp Release Publisher
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Building WebApp (npm run build)...
cd webapp
call npm run build
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] WebApp build failed!
    cd ..
    pause
    exit /b %errorlevel%
)
cd ..

echo.
echo [2/3] Packaging and publishing release to GitHub...
python scripts\publish_release.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Publishing failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Cleaning up temporary files...
if exist webapp-dist.tar.gz del webapp-dist.tar.gz

echo.
echo ========================================================
echo   Done! Restart your bot server in Pterodactyl.
echo ========================================================
echo.
pause
