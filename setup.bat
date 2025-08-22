@echo off
setlocal

REM Change to the directory where this script lives (your project root)
cd /d "%~dp0"

REM Path to venv python
set VENV_PY=.\.venv\Scripts\python.exe

REM 1. Create venv if it doesn't exist
if not exist ".venv\" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

REM 2. Upgrade pip to latest inside venv
echo [INFO] Upgrading pip...
%VENV_PY% -m pip install --upgrade pip

REM 3. Install requirements if file exists
if exist "requirements.txt" (
    echo [INFO] Installing from requirements.txt...
    %VENV_PY% -m pip install -r requirements.txt
) else (
    echo [WARN] requirements.txt not found. Skipping install.
)

echo [INFO] Setup complete. Virtual environment is ready.
echo To activate it, run:
echo   .venv\Scripts\activate
endlocal
pause
