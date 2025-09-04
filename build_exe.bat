@echo off
REM Always run from the directory of this batch file
cd /d "%~dp0"

REM Build script for maimai_data_scraper
echo === Cleaning old build... ===
rmdir /s /q build
rmdir /s /q dist
del /q maimai_data_scraper.spec

echo === Activating virtual environment ===
call .venv\Scripts\activate

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to activate virtual environment.
    echo Ensure the virtual environment exists and the path is correct.
    pause
    exit /b %ERRORLEVEL%
)

echo === Running PyInstaller ===
call pyinstaller --onefile --name maimai_data_scraper scraper\main.py

echo === Build finished ===
pause
