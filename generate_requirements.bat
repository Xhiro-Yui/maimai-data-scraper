@echo off
REM Always use the project's venv Python to freeze requirements
"%~dp0\.venv\Scripts\python.exe" -m pip freeze > "%~dp0\requirements.txt"
echo requirements.txt has been updated!
pause