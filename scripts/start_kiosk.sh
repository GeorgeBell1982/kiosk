#!/bin/bash
# Runtime launcher. Installation belongs in install/, not desktop startup.
set -e

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$PROJECT_DIR"

if [ "$(id -u)" -eq 0 ]; then
    echo "Run the kiosk as the desktop user, not root." >&2
    exit 1
fi

if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ] && \
   [ "${XDG_SESSION_TYPE:-}" != "wayland" ] && [ -z "${QT_QPA_PLATFORM:-}" ]; then
    echo "No graphical session found. Launch from the logged-in desktop." >&2
    exit 1
fi

if [ -d "$PROJECT_DIR/.venv" ]; then
    PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"
    if [ ! -x "$PYTHON_CMD" ]; then
        echo "The .venv interpreter is missing. Repair the environment before starting." >&2
        exit 1
    fi
else
    PYTHON_CMD="$(command -v python3)" || {
        echo "Python 3 is not installed." >&2
        exit 1
    }
fi

if ! "$PYTHON_CMD" -c 'from PyQt6.QtWidgets import QApplication; from PyQt6.QtWebEngineWidgets import QWebEngineView' ; then
    echo "Qt6 WebEngine is unavailable in $PYTHON_CMD." >&2
    echo "On Raspberry Pi run: bash install/quick_install_pyqt6.sh" >&2
    echo "For other systems, install requirements.txt in a Python virtual environment." >&2
    exit 1
fi

args=("$@")
if grep -q 'Raspberry Pi' /proc/cpuinfo 2>/dev/null; then
    fullscreen=false
    for arg in "${args[@]}"; do
        if [ "$arg" = "--fullscreen" ]; then fullscreen=true; fi
    done
    if [ "$fullscreen" = false ]; then args+=(--fullscreen); fi
fi

# The application checks for updates after obtaining its profile lock.
# exec preserves exit status and lets service managers signal the real browser.
exec "$PYTHON_CMD" "$PROJECT_DIR/kiosk_browser.py" "${args[@]}"
