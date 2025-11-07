@echo off
REM Deal Scout Shutdown Script
REM This script stops all services

echo ====================================
echo  Deal Scout Shutdown
echo ====================================
echo.

echo Stopping all services...
docker compose down

if errorlevel 1 (
    echo ERROR: Failed to stop services
    pause
    exit /b 1
)

echo.
echo ✓ All services stopped
echo.
pause
