@echo off
REM =========================================
REM Deal Scout - Stop Application
REM =========================================

echo.
echo ========================================
echo Stopping Deal Scout Application
echo ========================================
echo.

docker compose down

echo.
echo All services stopped.
echo.
echo To start again, run: start-app.bat
echo.
pause
