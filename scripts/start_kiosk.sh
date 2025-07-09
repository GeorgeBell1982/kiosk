#!/bin/bash
# Office Kiosk Browser Startup Script for Linux/Raspberry Pi
# This script activates the virtual environment and runs the kiosk browser

echo "Starting Office Kiosk Browser..."
echo

# Change to the project root directory (parent of scripts)
cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"

# Display version information
if [ -f "version.py" ]; then
    VERSION=$(python3 -c "import version; print(f'v{version.__version__} ({version.__build_date__})')" 2>/dev/null || echo "Unknown")
    echo "Version: $VERSION"
    echo
fi

# Set environment variables for GUI applications
export DISPLAY=${DISPLAY:-:0}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}

# Raspberry Pi specific display and GPU settings
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Configuring Raspberry Pi display settings..."
    
    # Set GPU memory split if not already configured
    GPU_MEMORY=$(vcgencmd get_mem gpu | cut -d= -f2 | cut -d M -f1)
    if [ "$GPU_MEMORY" -lt 64 ]; then
        echo "⚠ GPU memory is only ${GPU_MEMORY}MB. Recommend at least 64MB for better graphics."
        echo "  To fix: Add 'gpu_mem=64' to /boot/config.txt and reboot"
    fi
    
    # Disable Qt warnings and set better rendering
    export QT_LOGGING_RULES="*.debug=false;qt.qpa.screen=false"
    export QT_AUTO_SCREEN_SCALE_FACTOR=1
    export QT_SCALE_FACTOR=1
    export QT_SCREEN_SCALE_FACTORS=""
    
    # Force hardware acceleration and disable problematic features
    export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu-sandbox --disable-software-rasterizer --enable-gpu-rasterization --ignore-gpu-blacklist --disable-dev-shm-usage"
    
    # Disable EGL warnings
    export EGL_LOG_LEVEL=fatal
    export MESA_GL_VERSION_OVERRIDE=3.0
    
    # Ensure display is available
    if [ -z "$DISPLAY" ] || ! xset q &>/dev/null; then
        echo "⚠ Display not available or X11 not running"
        echo "  Make sure you're running in desktop mode, not SSH"
        echo "  Use: sudo raspi-config -> Boot Options -> Desktop Autologin"
    fi
fi

# Check for updates on Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Checking for updates..."
    if [ -f "scripts/update_check.sh" ]; then
        chmod +x scripts/update_check.sh
        ./scripts/update_check.sh
        
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
        # On Raspberry Pi, try Qt6 first, then fall back to Qt5
        echo "Installing system Qt packages..."
        if command -v apt >/dev/null 2>&1; then
            sudo apt update -qq 2>/dev/null || true
            
            # Try Qt6 first (for modern compatibility)
            if sudo apt install -y python3-pyqt6 python3-pyqt6.qtwebengine 2>/dev/null; then
                echo "✅ Qt6 packages installed"
                QT_VERSION="qt6"
            else
                echo "Qt6 not available, installing Qt5..."
                sudo apt install -y python3-pyqt5 python3-pyqt5.qtwebengine python3-pyqt5.qtwebkit 2>/dev/null || true
                QT_VERSION="qt5"
            fi
        fi
        
        # Create venv with system site packages for Qt access
        python3 -m venv --system-site-packages .venv
        echo "Installing additional dependencies (using system Qt packages)..."
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

# Test Qt versions and determine which to use
echo "Testing Qt compatibility..."
QT_TO_USE="none"

# Test Qt6 first (preferred)
if $PYTHON_CMD -c "import PyQt6.QtWidgets; print('✅ Qt6 available')" 2>/dev/null; then
    if $PYTHON_CMD -c "import PyQt6.QtWebEngineWidgets; print('✅ Qt6 WebEngine available')" 2>/dev/null; then
        echo "🎉 Using Qt6 - best modern web compatibility!"
        QT_TO_USE="qt6"
        KIOSK_SCRIPT="kiosk_browser.py"
    else
        echo "⚠️ Qt6 available but WebEngine missing"
    fi
fi

# Fallback to Qt5 if Qt6 not available or incomplete
if [ "$QT_TO_USE" = "none" ] && $PYTHON_CMD -c "import PyQt5.QtWidgets; print('✅ Qt5 available')" 2>/dev/null; then
    if $PYTHON_CMD -c "import PyQt5.QtWebEngineWidgets; print('✅ Qt5 WebEngine available')" 2>/dev/null; then
        echo "⚠️ Using Qt5 - consider upgrading to Qt6 for better YouTube support"
        QT_TO_USE="qt5"
        # Use Qt5 backup if main file is Qt6
        if [ -f "kiosk_browser_qt5_backup.py" ]; then
            KIOSK_SCRIPT="kiosk_browser_qt5_backup.py"
        else
            KIOSK_SCRIPT="kiosk_browser.py"
        fi
    elif $PYTHON_CMD -c "import PyQt5.QtWebKit; print('✅ Qt5 WebKit available')" 2>/dev/null; then
        echo "⚠️ Using Qt5 WebKit - limited modern web support"
        QT_TO_USE="qt5_webkit"
        KIOSK_SCRIPT="kiosk_browser_qt5_backup.py"
    fi
fi

# If no Qt version works, try to install
if [ "$QT_TO_USE" = "none" ]; then
    echo "❌ No compatible Qt version found!"
    echo "Attempting to install Qt packages..."
    
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        echo "Installing system Qt packages..."
        sudo apt install -y python3-pyqt6 python3-pyqt6.qtwebengine 2>/dev/null || \
        sudo apt install -y python3-pyqt5 python3-pyqt5.qtwebengine 2>/dev/null || true
        
        # Try system python if venv python fails
        if ! $PYTHON_CMD -c "import PyQt6.QtWidgets" 2>/dev/null && ! $PYTHON_CMD -c "import PyQt5.QtWidgets" 2>/dev/null; then
            echo "Using system Python as fallback..."
            PYTHON_CMD="python3"
        fi
    else
        # Try pip install as fallback
        $PYTHON_CMD -m pip install PyQt6 PyQt6-WebEngine 2>/dev/null || \
        $PYTHON_CMD -m pip install PyQt5 PyQtWebEngine 2>/dev/null || \
        $PYTHON_CMD -m pip install PyQt5 PyQtWebKit 2>/dev/null || true
    fi
    
    # Re-test after installation attempt
    if $PYTHON_CMD -c "import PyQt6.QtWidgets" 2>/dev/null; then
        QT_TO_USE="qt6"
        KIOSK_SCRIPT="kiosk_browser.py"
    elif $PYTHON_CMD -c "import PyQt5.QtWidgets" 2>/dev/null; then
        QT_TO_USE="qt5"
        KIOSK_SCRIPT="kiosk_browser_qt5_backup.py"
    else
        echo "❌ Qt still not available. Please install manually:"
        echo "   For Qt6: sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine"
        echo "   For Qt5: sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine"
        echo "   Or run: ./scripts/debug_startup.sh"
        echo "   Or run: python3 test_qt_version.py"
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

# Run the application with the determined Python command and script
echo "Starting kiosk browser with: $PYTHON_CMD $KIOSK_SCRIPT ($QT_TO_USE)"
$PYTHON_CMD $KIOSK_SCRIPT $ARGS

echo
echo "Office Kiosk Browser has stopped."
