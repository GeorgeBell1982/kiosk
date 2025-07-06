# Office Kiosk Browser PowerShell Launcher
# This script provides a more robust way to launch the kiosk browser on Windows

param(
    [switch]$Fullscreen,
    [switch]$Help
)

if ($Help) {
    Write-Host "Office Kiosk Browser Launcher" -ForegroundColor Green
    Write-Host "Usage: .\start_kiosk.ps1 [-Fullscreen] [-Help]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Fullscreen    Start in fullscreen mode"
    Write-Host "  -Help          Show this help message"
    exit 0
}

Write-Host "Starting Office Kiosk Browser..." -ForegroundColor Green
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to the script directory
Set-Location $ScriptDir

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
    
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & ".venv\Scripts\pip.exe" install -r requirements.txt
}

# Prepare arguments
$appArgs = @()
if ($Fullscreen) {
    $appArgs += "--fullscreen"
}

# Run the application
Write-Host "Launching browser..." -ForegroundColor Green
& ".venv\Scripts\python.exe" "kiosk_browser.py" @appArgs

Write-Host ""
Write-Host "Office Kiosk Browser has stopped." -ForegroundColor Yellow
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
