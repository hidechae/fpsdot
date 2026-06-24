@echo off
REM Local build: produces dist\fpsdot.exe via PyInstaller.
REM Assumes .venv has been created by run.bat at least once.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo .venv not found. Run run.bat once first to create it.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install --upgrade pyinstaller || exit /b 1

if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist fpsdot.spec del /q fpsdot.spec

".venv\Scripts\python.exe" -m PyInstaller --noconsole --onefile --name fpsdot --paths src src\main.py || exit /b 1

echo.
echo Build complete: dist\fpsdot.exe
exit /b 0
