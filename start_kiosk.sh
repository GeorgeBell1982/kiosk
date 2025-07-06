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
    python3 -m venv .venv
    
    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt
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

# Activate virtual environment and run the application
.venv/bin/python kiosk_browser.py $ARGS

echo
echo "Office Kiosk Browser has stopped."
