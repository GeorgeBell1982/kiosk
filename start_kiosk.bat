@echo off
REM Office Kiosk Browser Startup Script for Windows
REM This script activates the virtual environment and runs the kiosk browser

echo Starting Office Kiosk Browser...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Activate virtual environment and run the application
.venv\Scripts\python.exe kiosk_browser.py %*

echo.
echo Office Kiosk Browser has stopped.
pause
