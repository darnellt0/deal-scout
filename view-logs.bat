@echo off
REM Deal Scout Logs Viewer
REM This script shows logs from all services

echo ====================================
echo  Deal Scout Logs
echo ====================================
echo.
echo Select a service to view logs:
echo.
echo 1. All services
echo 2. Backend
echo 3. Frontend
echo 4. Worker (Celery)
echo 5. Beat (Scheduler)
echo 6. Postgres
echo 7. Redis
echo.

set /p CHOICE="Enter your choice (1-7): "

if "%CHOICE%"=="1" (
    docker compose logs -f --tail=100
) else if "%CHOICE%"=="2" (
    docker compose logs -f backend --tail=100
) else if "%CHOICE%"=="3" (
    docker compose logs -f frontend --tail=100
) else if "%CHOICE%"=="4" (
    docker compose logs -f worker --tail=100
) else if "%CHOICE%"=="5" (
    docker compose logs -f beat --tail=100
) else if "%CHOICE%"=="6" (
    docker compose logs -f postgres --tail=100
) else if "%CHOICE%"=="7" (
    docker compose logs -f redis --tail=100
) else (
    echo Invalid choice. Showing all logs...
    docker compose logs -f --tail=100
)
