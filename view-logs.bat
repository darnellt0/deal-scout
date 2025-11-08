@echo off
REM =========================================
REM Deal Scout - View Logs
REM =========================================

echo.
echo ========================================
echo Deal Scout - Service Logs
echo ========================================
echo.
echo Choose a service to view logs:
echo.
echo 1. All services
echo 2. Backend (API)
echo 3. Frontend (UI)
echo 4. Database (PostgreSQL)
echo 5. Cache (Redis)
echo.

choice /C 12345 /M "Select option"

if %errorlevel% equ 1 (
    echo.
    echo Showing logs for all services (Ctrl+C to exit)...
    docker compose logs -f
)

if %errorlevel% equ 2 (
    echo.
    echo Showing backend logs (Ctrl+C to exit)...
    docker compose logs -f backend
)

if %errorlevel% equ 3 (
    echo.
    echo Showing frontend logs (Ctrl+C to exit)...
    docker compose logs -f frontend
)

if %errorlevel% equ 4 (
    echo.
    echo Showing database logs (Ctrl+C to exit)...
    docker compose logs -f postgres
)

if %errorlevel% equ 5 (
    echo.
    echo Showing redis logs (Ctrl+C to exit)...
    docker compose logs -f redis
)
