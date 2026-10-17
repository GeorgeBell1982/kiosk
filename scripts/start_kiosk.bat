@echo off
setlocal
pushd "%~dp0.." || exit /b 1
set "PYTHON_CMD=python"
if exist ".venv\" (
    if not exist ".venv\Scripts\python.exe" (
        echo The .venv interpreter is missing. Repair the environment before starting.
        popd
        exit /b 1
    )
    set "PYTHON_CMD=%CD%\.venv\Scripts\python.exe"
)
"%PYTHON_CMD%" -c "from PyQt6.QtWidgets import QApplication; from PyQt6.QtWebEngineWidgets import QWebEngineView"
if errorlevel 1 (
    echo Qt6 WebEngine is unavailable. Install requirements.txt in the selected Python environment.
    popd
    exit /b 1
)
"%PYTHON_CMD%" "%CD%\kiosk_browser.py" %*
set "KIOSK_EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %KIOSK_EXIT_CODE%
