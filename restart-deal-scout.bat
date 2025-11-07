@echo off
REM Deal Scout Restart Script
REM This script restarts all services

echo ====================================
echo  Deal Scout Restart
echo ====================================
echo.

echo Stopping services...
docker compose down

echo.
echo Starting services...
docker compose up -d

echo.
echo Waiting for backend to be ready...
set MAX_RETRIES=30
set RETRY_COUNT=0

:WAIT_LOOP
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/ping >nul 2>&1
if errorlevel 1 (
    set /a RETRY_COUNT+=1
    if %RETRY_COUNT% LSS %MAX_RETRIES% (
        echo    Waiting... attempt %RETRY_COUNT%/%MAX_RETRIES%
        goto WAIT_LOOP
    ) else (
        echo ERROR: Backend did not start within 60 seconds
        pause
        exit /b 1
    )
)

echo.
echo ✓ Deal Scout restarted successfully
echo.
echo Services:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo.
pause
