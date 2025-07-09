#!/bin/bash
# Test script for wvkbd virtual keyboard on Raspberry Pi Wayland/Bookworm

echo "Testing Virtual Keyboard (wvkbd) on Raspberry Pi"
echo "================================================"
echo

# Check environment
echo "🔍 Environment Check:"
echo "  XDG_SESSION_TYPE: ${XDG_SESSION_TYPE:-not set}"
echo "  WAYLAND_DISPLAY: ${WAYLAND_DISPLAY:-not set}"
echo "  DISPLAY: ${DISPLAY:-not set}"
echo

# Check if wvkbd is installed
echo "📦 Checking wvkbd installation:"
if command -v wvkbd-mobintl >/dev/null 2>&1; then
    echo "  ✅ wvkbd-mobintl found at: $(which wvkbd-mobintl)"
else
    echo "  ❌ wvkbd-mobintl not found"
    echo "  Installing wvkbd..."
    sudo apt update -qq
    sudo apt install -y wvkbd
    
    if command -v wvkbd-mobintl >/dev/null 2>&1; then
        echo "  ✅ wvkbd-mobintl installed successfully"
    else
        echo "  ❌ wvkbd installation failed"
        exit 1
    fi
fi
echo

# Check if keyboard is already running
echo "🔄 Checking if keyboard is already running:"
if pgrep wvkbd-mobintl >/dev/null; then
    echo "  ⚠️  Keyboard already running, stopping it first..."
    pkill wvkbd-mobintl
    sleep 1
fi
echo "  ✅ No keyboard processes running"
echo

# Test basic keyboard functionality
echo "🧪 Testing basic keyboard (5 seconds):"
echo "  Starting wvkbd-mobintl with basic settings..."

# Detect Wayland vs X11
if [ -n "$WAYLAND_DISPLAY" ] || [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "  📡 Wayland detected - using Wayland-optimized settings"
    wvkbd-mobintl --landscape --height 300 --margin 10 --bg 333333cc --fg ffffff --alpha 0.9 &
else
    echo "  🖥️  X11 detected - using X11 settings"
    wvkbd-mobintl --landscape --height 280 --margin 5 --fg white --layer overlay &
fi

KEYBOARD_PID=$!
sleep 1

# Check if keyboard started
if pgrep wvkbd-mobintl >/dev/null; then
    echo "  ✅ Keyboard started successfully (PID: $KEYBOARD_PID)"
    echo "  👀 You should see a virtual keyboard on your screen"
    echo "  ⏳ Waiting 5 seconds..."
    sleep 5
    
    # Stop keyboard
    echo "  🔄 Stopping keyboard..."
    pkill wvkbd-mobintl
    wait $KEYBOARD_PID 2>/dev/null
    echo "  ✅ Keyboard stopped"
else
    echo "  ❌ Keyboard failed to start"
    echo "  🔍 Process not found in process list"
fi
echo

echo "🎯 Manual test commands:"
echo "  Basic test:     wvkbd-mobintl --landscape"
echo "  Wayland test:   wvkbd-mobintl --landscape --height 300 --bg 333333cc --fg ffffff"
echo "  Kill keyboard:  pkill wvkbd-mobintl"
echo

echo "📝 If keyboard doesn't appear:"
echo "  1. Make sure you're in desktop mode (not SSH)"
echo "  2. Try switching to a different virtual terminal and back (Ctrl+Alt+F2, then Ctrl+Alt+F7)"
echo "  3. Check compositor logs: journalctl -u gdm"
echo "  4. Try alternative: sudo apt install onboard && onboard"
echo

echo "Test completed!"
