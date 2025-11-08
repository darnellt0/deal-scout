@echo off
REM =========================================
REM Deal Scout - Create User Account
REM =========================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Deal Scout - User Account Creation
echo ========================================
echo.

REM Check if backend is running
curl -s http://localhost:8000/health >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Backend is not running!
    echo.
    echo Please start the application first:
    echo   start-app.bat
    echo.
    pause
    exit /b 1
)

echo Backend is running. Let's create your user account.
echo.

REM Get user input
set /p USERNAME="Username: "
if "!USERNAME!"=="" (
    echo Username cannot be empty
    pause
    exit /b 1
)

set /p EMAIL="Email: "
if "!EMAIL!"=="" (
    echo Email cannot be empty
    pause
    exit /b 1
)

REM Get password (note: will be visible on screen - limitation of batch files)
echo.
echo NOTE: Password will be visible on screen
set /p PASSWORD="Password (min 8 characters): "
if "!PASSWORD!"=="" (
    echo Password cannot be empty
    pause
    exit /b 1
)

set /p FIRSTNAME="First Name (optional): "
if "!FIRSTNAME!"=="" set FIRSTNAME=User

set /p LASTNAME="Last Name (optional): "
if "!LASTNAME!"=="" set LASTNAME=Admin

echo.
echo Creating user...
echo.

REM Create JSON payload and call API
echo {"username":"!USERNAME!","email":"!EMAIL!","password":"!PASSWORD!","first_name":"!FIRSTNAME!","last_name":"!LASTNAME!"} > temp_user.json

curl -X POST http://localhost:8000/auth/register ^
  -H "Content-Type: application/json" ^
  -d @temp_user.json

del temp_user.json

echo.
echo.

if %errorlevel% equ 0 (
    echo ========================================
    echo User Created Successfully!
    echo ========================================
    echo.
    echo You can now login at:
    echo   http://localhost:3000
    echo.
    echo Login with:
    echo   Username: !USERNAME!
    echo   Password: [the password you entered]
    echo.
) else (
    echo ========================================
    echo User Creation Failed
    echo ========================================
    echo.
    echo Common issues:
    echo   - Username or email already exists
    echo   - Password doesn't meet requirements
    echo   - Backend service not ready
    echo.
    echo Try again or check logs: docker compose logs backend
    echo.
)

pause
