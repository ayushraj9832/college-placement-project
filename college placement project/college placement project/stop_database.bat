@echo off
REM Stops the project's own MySQL instance (port 3307).
setlocal
cd /d "%~dp0"

set "MYSQLADMIN=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqladmin.exe"
if not exist "%MYSQLADMIN%" for /f "delims=" %%i in ('where mysqladmin 2^>nul') do set "MYSQLADMIN=%%i"

"%MYSQLADMIN%" -h 127.0.0.1 -P 3307 -u root shutdown
if errorlevel 1 (
    echo MySQL was not running on port 3307.
) else (
    echo MySQL stopped.
)
