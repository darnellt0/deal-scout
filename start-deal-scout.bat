@echo off
REM Deal Scout Startup Script
REM This script starts all services and sets up user accounts

echo ====================================
echo  Deal Scout Startup
echo ====================================
echo.

REM Check if Docker is running
echo [1/5] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo ✓ Docker is running

REM Start all services
echo.
echo [2/5] Starting all services...
docker compose up -d
if errorlevel 1 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)
echo ✓ Services started

REM Wait for backend to be ready
echo.
echo [3/5] Waiting for backend to be ready...
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
        echo.
        echo Showing backend logs:
        docker compose logs backend --tail=50
        pause
        exit /b 1
    )
)
echo ✓ Backend is ready

REM Create user accounts
echo.
echo [4/5] Creating user accounts...
python scripts\create_users.py
if errorlevel 1 (
    echo WARNING: Failed to create users with 'python' command
    echo Trying 'py' command...
    py scripts\create_users.py
    if errorlevel 1 (
        echo WARNING: Could not create users automatically
        echo You may need to create them manually or users may already exist
    ) else (
        echo ✓ User accounts created
    )
) else (
    echo ✓ User accounts created
)

REM Show status
echo.
echo [5/5] Checking service status...
docker compose ps
echo.

echo ====================================
echo  Deal Scout is Ready!
echo ====================================
echo.
echo Services:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   MailHog:   http://localhost:8025
echo.
echo Login Credentials:
echo   Username: seller1
echo   Password: Password123!
echo.
echo   Username: seller2
echo   Password: Password123!
echo.

REM Ask if user wants to open browser
set /p OPEN_BROWSER="Open login page in browser? (Y/N): "
if /i "%OPEN_BROWSER%"=="Y" (
    start http://localhost:3000/login
)

echo.
echo Press any key to exit (services will continue running)...
pause >nul
