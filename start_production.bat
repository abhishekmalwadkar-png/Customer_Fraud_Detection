@echo off
REM ============================================================================
REM Dummy Bank Portal - Production Server Launcher (Node.js + Express)
REM High-Concurrency Gateway with PostgreSQL Connection Pooling
REM ============================================================================

title Dummy Bank Portal - Fraud Detection Portal (Node.js + Express)

echo ============================================================================
echo   DUMMY BANK PORTAL - FRAUD OPERATIONS SYSTEM
echo   Starting Production Server (Node.js + Express + pg.Pool)
echo ============================================================================
echo.

REM Verify Node.js environment
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not found in system PATH. Please install Node.js 18+
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from .env.example...
    copy .env.example .env
    echo [!] Please update database credentials in .env and restart.
)

REM Check if node_modules exists
if not exist node_modules (
    echo [*] Installing Node.js dependencies...
    call npm.cmd install
)

echo.
echo [*] Launching Production Node.js Server...
echo [*] Web Portal UI:   http://127.0.0.1:5050
echo [*] SOC Operations:  http://127.0.0.1:5050/login.html
echo [*] Customer Portal: http://127.0.0.1:5050/customer.html
echo [*] API Health:      http://127.0.0.1:5050/health
echo [*] API Metrics:     http://127.0.0.1:5050/api/metrics
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================================
echo.

node server.js
pause
