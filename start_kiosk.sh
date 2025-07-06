#!/bin/bash
# Office Kiosk Browser Startup Script for Linux/Raspberry Pi
# This script activates the virtual environment and runs the kiosk browser

echo "Starting Office Kiosk Browser..."
echo

# Change to the script directory
cd "$(dirname "$0")"

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
