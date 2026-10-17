# Runtime launcher: use the installed environment and propagate browser failures.
param(
    [switch]$Fullscreen,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
if ($Help) {
    Write-Host 'Usage: .\scripts\start_kiosk.ps1 [-Fullscreen] [-Help]'
    exit 0
}

$ProjectDir = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $ProjectDir
try {
    if (Test-Path -LiteralPath '.venv') {
        $PythonCmd = Join-Path $ProjectDir '.venv\Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $PythonCmd -PathType Leaf)) {
            throw 'The .venv interpreter is missing. Repair the environment before starting.'
        }
    } else {
        $PythonCmd = (Get-Command python -CommandType Application -ErrorAction Stop).Source
    }
    & $PythonCmd -c 'from PyQt6.QtWidgets import QApplication; from PyQt6.QtWebEngineWidgets import QWebEngineView'
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Qt6 WebEngine is unavailable. Install requirements.txt in the selected Python environment.'
    }
    $BrowserArgs = @()
    if ($Fullscreen) { $BrowserArgs += '--fullscreen' }
    & $PythonCmd (Join-Path $ProjectDir 'kiosk_browser.py') @BrowserArgs
    $BrowserExitCode = $LASTEXITCODE
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    $BrowserExitCode = 1
} finally {
    Pop-Location
}
exit $BrowserExitCode
