@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

REM ============================================================
REM fpsdot launcher
REM ------------------------------------------------------------
REM 1. Locate a usable Python (not the Microsoft Store stub).
REM 2. Create .venv + install requirements on first run.
REM 3. Launch src\main.py with python.exe (console visible) so
REM    any startup errors are not silently swallowed.
REM    Use run-silent.bat once you have confirmed it works.
REM ============================================================

set "PY_EXE="

REM --- (1) Try py launcher (python.org installer ships this) ---
where py >nul 2>&1
if !errorlevel! equ 0 (
    py -3 -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 set "PY_EXE=py -3"
)

REM --- (2) Try python.exe NOT under WindowsApps (stub) ---
if not defined PY_EXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        echo %%i | findstr /v /i "WindowsApps" >nul
        if !errorlevel! equ 0 (
            set "PY_EXE=%%i"
            goto :have_python
        )
    )
)

REM --- (3) Try common install paths after a winget install ---
if not defined PY_EXE (
    for %%V in (312 311 310 313) do (
        if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
            set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
            goto :have_python
        )
        if exist "C:\Python%%V\python.exe" (
            set "PY_EXE=C:\Python%%V\python.exe"
            goto :have_python
        )
        if exist "C:\Program Files\Python%%V\python.exe" (
            set "PY_EXE=C:\Program Files\Python%%V\python.exe"
            goto :have_python
        )
    )
)

:have_python
if not defined PY_EXE goto :need_python

echo Using Python: %PY_EXE%

REM --- (4) Create venv + install deps on first run ---
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment ...
    %PY_EXE% -m venv .venv || goto :err
    echo Installing dependencies ...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip || goto :err
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :err
)

REM --- (5) Launch (console visible) ---
echo.
echo Starting fpsdot ... (close this window to stop)
".venv\Scripts\python.exe" "src\main.py"
set "EC=!errorlevel!"
echo.
echo fpsdot exited with code !EC!.
pause
exit /b !EC!

:need_python
echo.
echo ============================================================
echo  Python 3.10+ was NOT found.
echo.
echo  The only "python.exe" on this system is the Microsoft Store
echo  stub, which cannot create a venv.
echo.
echo  Options:
echo    A) Install via winget (recommended):
echo         winget install -e --id Python.Python.3.12
echo    B) Download from https://www.python.org/downloads/
echo       (Be sure to check "Add python.exe to PATH" during install.)
echo.
echo  After installing, OPEN A NEW terminal and run this script again.
echo ============================================================
echo.

where winget >nul 2>&1
if !errorlevel! neq 0 (
    pause
    exit /b 1
)

choice /c YN /n /m "Install Python 3.12 now via winget? [Y/N] "
if !errorlevel! equ 1 (
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    echo.
    echo Install finished. Close this window and re-run run.bat.
)
pause
exit /b 1

:err
echo.
echo Setup failed. See messages above.
pause
exit /b 1
