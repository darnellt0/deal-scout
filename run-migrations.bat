@echo off
REM =========================================
REM Deal Scout - Run Database Migrations
REM =========================================

echo.
echo ========================================
echo Running Database Migrations
echo ========================================
echo.

REM Check if services are running
docker compose ps | findstr "backend" >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Services are not running
    echo.
    echo Please start the application first:
    echo   start-app.bat
    echo.
    pause
    exit /b 1
)

echo Current migration status:
echo.
docker compose exec backend alembic current
echo.

echo ========================================
echo Applying all pending migrations...
echo ========================================
echo.

docker compose exec backend alembic upgrade head

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Migrations Completed Successfully!
    echo ========================================
    echo.
    echo Current version:
    docker compose exec backend alembic current
    echo.
) else (
    echo.
    echo ========================================
    echo Migration Failed
    echo ========================================
    echo.
    echo Check the logs for errors:
    echo   docker compose logs backend
    echo.
)

pause
