#!/bin/bash
# Office Kiosk Browser Startup Script for Linux/Raspberry Pi
# This script activates the virtual environment and runs the kiosk browser

echo "Starting Office Kiosk Browser..."
echo

# Display version information
if [ -f "version.py" ]; then
    VERSION=$(python3 -c "import version; print(f'v{version.__version__} ({version.__build_date__})')" 2>/dev/null || echo "Unknown")
    echo "Version: $VERSION"
    echo
fi

# Change to the script directory
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

# Set environment variables for GUI applications
export DISPLAY=${DISPLAY:-:0}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}

# Check for updates on Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Checking for updates..."
    if [ -f "update_check.sh" ]; then
        chmod +x update_check.sh
        ./update_check.sh
        
        # Check if restart is needed after update
        if [ -f "/tmp/kiosk-restart-needed" ]; then
            rm -f /tmp/kiosk-restart-needed
            echo "Updates were applied. Restarting with new version..."
            echo
        fi
    fi
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        # On Raspberry Pi, try system packages first, then create venv with system site packages
        echo "Installing system PyQt5 packages..."
        if command -v apt >/dev/null 2>&1; then
            sudo apt update -qq 2>/dev/null || true
            sudo apt install -y python3-pyqt5 python3-pyqt5.qtwebengine python3-pyqt5.qtwebkit 2>/dev/null || true
        fi
        
        # Create venv with system site packages for PyQt5 access
        python3 -m venv --system-site-packages .venv
        echo "Installing additional dependencies (using system PyQt5)..."
        if [ -f "requirements-rpi.txt" ]; then
            .venv/bin/pip install -r requirements-rpi.txt
        fi
    else
        # On other systems, use standard venv and requirements
        python3 -m venv .venv
        echo "Installing dependencies..."
        .venv/bin/pip install -r requirements.txt
    fi
fi

# Ensure virtual environment is properly activated and working
if [ ! -f ".venv/bin/python" ]; then
    echo "❌ Virtual environment creation failed!"
    echo "Trying to run with system Python..."
    PYTHON_CMD="python3"
else
    echo "✅ Using virtual environment"
    PYTHON_CMD=".venv/bin/python"
fi

# Test PyQt5 import before starting
echo "Testing PyQt5 import..."
if ! $PYTHON_CMD -c "import PyQt5.QtWidgets; print('✅ PyQt5 import successful')" 2>/dev/null; then
    echo "❌ PyQt5 import failed!"
    echo "Attempting to install PyQt5..."
    
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        echo "Installing system PyQt5 packages..."
        sudo apt install -y python3-pyqt5 python3-pyqt5.qtwebengine python3-pyqt5.qtwebkit 2>/dev/null || true
        
        # Try system python if venv python fails
        if ! $PYTHON_CMD -c "import PyQt5.QtWidgets" 2>/dev/null; then
            echo "Using system Python as fallback..."
            PYTHON_CMD="python3"
        fi
    else
        # Try pip install as fallback
        $PYTHON_CMD -m pip install PyQt5 PyQtWebEngine 2>/dev/null || $PYTHON_CMD -m pip install PyQt5 PyQtWebKit 2>/dev/null || true
    fi
    
    # Final test
    if ! $PYTHON_CMD -c "import PyQt5.QtWidgets" 2>/dev/null; then
        echo "❌ PyQt5 still not available. Please install manually:"
        echo "   sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine"
        echo "   or run: ./debug_startup.sh"
        exit 1
    fi
fi

# Check if running on Raspberry Pi and automatically add fullscreen
ARGS="$@"
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Raspberry Pi detected - starting in fullscreen mode"
    # Only add --fullscreen if not already specified
    if [[ ! "$ARGS" =~ "--fullscreen" ]]; then
        ARGS="$ARGS --fullscreen"
    fi
fi

# Run the application with the determined Python command
echo "Starting kiosk browser with: $PYTHON_CMD"
$PYTHON_CMD kiosk_browser.py $ARGS

echo
echo "Office Kiosk Browser has stopped."
