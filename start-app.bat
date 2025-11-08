@echo off
REM =========================================
REM Deal Scout - Complete Startup Script
REM =========================================
REM This script starts the application and sets it up

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Deal Scout - Starting Application
echo ========================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo [1/5] Stopping any existing containers...
docker compose down

echo.
echo [2/5] Starting services (this may take 1-2 minutes)...
echo       - PostgreSQL database
echo       - Redis cache
echo       - Backend API (FastAPI)
echo       - Frontend UI (Next.js)
echo.
docker compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services
    echo.
    echo Check logs with: docker compose logs
    pause
    exit /b 1
)

echo.
echo [3/5] Waiting for services to be ready (30 seconds)...
timeout /t 30 /nobreak >nul

echo.
echo [4/5] Running database migrations...
docker compose exec -T backend alembic upgrade head

if %errorlevel% neq 0 (
    echo [WARNING] Migrations may have failed
    echo You can run them manually later with:
    echo   docker compose exec backend alembic upgrade head
)

echo.
echo [5/5] Checking service status...
docker compose ps

echo.
echo ========================================
echo Services Started Successfully!
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend UI:  http://localhost:3000
echo.
echo ========================================
echo NEXT STEP: Create Your First User
echo ========================================
echo.
echo Option 1: Run the user creation script
echo   create-user.bat
echo.
echo Option 2: Use the API directly
echo   See QUICK_START.md for details
echo.
echo Option 3: Register through the UI
echo   Go to http://localhost:3000 and look for register option
echo.
echo ========================================
echo.

choice /C YN /M "Would you like to create a user now"
if %errorlevel% equ 1 (
    echo.
    echo Launching user creation...
    call create-user.bat
) else (
    echo.
    echo You can create a user later by running: create-user.bat
)

echo.
echo To view logs, run: docker compose logs -f
echo To stop services, run: docker compose down
echo.
pause
