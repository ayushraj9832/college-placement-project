@echo off
REM ===================================================================
REM  College Placement and Recruitment Management System
REM  One-click setup and run script for Windows.
REM
REM  First run : creates .venv, installs requirements, copies .env
REM  Later runs: just starts the Flask development server
REM ===================================================================
setlocal
cd /d "%~dp0"

REM If this copy of the project has its own MySQL data folder, start it first.
if exist "mysql-data\data" call "%~dp0start_database.bat"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH.
    echo Install Python 3.10 or newer from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment already exists.
)

if not exist ".env" (
    echo [2/3] Creating .env from .env.example ...
    copy /y ".env.example" ".env" >nul
    echo      Open .env and set DB_PASSWORD before logging in.
) else (
    echo [2/3] .env already exists.
)

echo [3/3] Installing dependencies (safe to re-run) ...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo Starting Flask on http://127.0.0.1:5000  (press Ctrl+C to stop)
echo.
".venv\Scripts\python.exe" app.py

pause
endlocal
