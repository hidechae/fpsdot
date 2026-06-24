@echo off
REM Silent launcher — for everyday use AFTER first successful run with run.bat.
REM Uses pythonw.exe so no console window appears.
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo .venv not found. Please run run.bat once first.
    pause
    exit /b 1
)

start "" /b ".venv\Scripts\pythonw.exe" "src\main.py"
exit /b 0
