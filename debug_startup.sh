#!/bin/bash
# Debug script for Office Kiosk Browser startup issues

echo "Office Kiosk Browser - Startup Debugging"
echo "========================================"
echo "Run this script on the Raspberry Pi to diagnose startup issues"
echo

# Check if we're on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This appears to not be a Raspberry Pi"
    echo
fi

echo "=== 1. AUTOSTART FILE CHECK ==="
LXDE_AUTOSTART="$HOME/.config/lxsession/LXDE-pi/autostart"
if [ -f "$LXDE_AUTOSTART" ]; then
    echo "✓ LXDE autostart file exists: $LXDE_AUTOSTART"
    echo "Contents:"
    cat "$LXDE_AUTOSTART" | nl
    echo
    
    if grep -q "office_kiosk\|kiosk" "$LXDE_AUTOSTART" 2>/dev/null; then
        echo "✓ Kiosk entry found in autostart"
    else
        echo "✗ No kiosk entry found in autostart file"
    fi
else
    echo "✗ LXDE autostart file missing: $LXDE_AUTOSTART"
fi
echo

echo "=== 2. PROJECT FILES CHECK ==="
PROJECT_DIR="/home/pi/office_kiosk"
START_SCRIPT="$PROJECT_DIR/start_kiosk.sh"
MAIN_SCRIPT="$PROJECT_DIR/kiosk_browser.py"

if [ -d "$PROJECT_DIR" ]; then
    echo "✓ Project directory exists: $PROJECT_DIR"
    echo "Contents:"
    ls -la "$PROJECT_DIR" | head -20
    echo
else
    echo "✗ Project directory missing: $PROJECT_DIR"
fi

if [ -f "$START_SCRIPT" ]; then
    echo "✓ Start script exists: $START_SCRIPT"
    if [ -x "$START_SCRIPT" ]; then
        echo "✓ Start script is executable"
    else
        echo "✗ Start script is not executable"
        echo "  Fix with: chmod +x $START_SCRIPT"
    fi
else
    echo "✗ Start script missing: $START_SCRIPT"
fi

if [ -f "$MAIN_SCRIPT" ]; then
    echo "✓ Main Python script exists: $MAIN_SCRIPT"
else
    echo "✗ Main Python script missing: $MAIN_SCRIPT"
fi
echo

echo "=== 3. PYTHON ENVIRONMENT CHECK ==="
echo "Python version:"
python3 --version
echo

echo "Testing PyQt5 import:"
if python3 -c "import PyQt5.QtWidgets; print('PyQt5 import: SUCCESS')" 2>/dev/null; then
    echo "✓ PyQt5 is working"
else
    echo "✗ PyQt5 import failed"
    echo "Error details:"
    python3 -c "import PyQt5.QtWidgets" 2>&1 || true
fi
echo

echo "=== 4. DISPLAY ENVIRONMENT CHECK ==="
echo "DISPLAY variable: ${DISPLAY:-'NOT SET'}"
echo "XDG_CURRENT_DESKTOP: ${XDG_CURRENT_DESKTOP:-'NOT SET'}"
echo "DESKTOP_SESSION: ${DESKTOP_SESSION:-'NOT SET'}"
echo

if command -v xset >/dev/null 2>&1; then
    echo "Testing X11 connection:"
    if xset q >/dev/null 2>&1; then
        echo "✓ X11 connection working"
    else
        echo "✗ X11 connection failed"
    fi
else
    echo "✗ xset command not found"
fi
echo

echo "=== 5. MANUAL STARTUP TEST ==="
echo "Testing manual startup..."
cd "$PROJECT_DIR" 2>/dev/null || {
    echo "✗ Cannot change to project directory"
    exit 1
}

if [ -f "$START_SCRIPT" ] && [ -x "$START_SCRIPT" ]; then
    echo "Running: $START_SCRIPT --help"
    timeout 10s "$START_SCRIPT" --help 2>&1 || {
        echo "✗ Start script test failed or timed out"
        echo "Try running manually: cd $PROJECT_DIR && $START_SCRIPT"
    }
else
    echo "✗ Cannot test start script (missing or not executable)"
fi
echo

echo "=== 6. SYSTEM LOGS CHECK ==="
echo "Recent error logs (last 10 minutes):"
journalctl --since "10 minutes ago" --no-pager | grep -i "error\|fail\|python\|kiosk" | tail -10 || echo "No recent errors found"
echo

echo "=== 7. AUTO-UPDATE STATUS ==="
UPDATE_SCRIPT="$PROJECT_DIR/update_check.sh"
if [ -f "$UPDATE_SCRIPT" ]; then
    echo "✓ Update script exists: $UPDATE_SCRIPT"
    if [ -x "$UPDATE_SCRIPT" ]; then
        echo "✓ Update script is executable"
    else
        echo "✗ Update script is not executable"
        echo "  Fix with: chmod +x $UPDATE_SCRIPT"
    fi
else
    echo "✗ Update script missing: $UPDATE_SCRIPT"
fi
echo

echo "=== RECOMMENDATIONS ==="
echo "1. If autostart file is missing, run: ./troubleshoot_autostart.sh"
echo "2. If PyQt5 import fails, run: sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine"
echo "3. If X11 connection fails, ensure you're running in desktop mode, not SSH"
echo "4. For manual testing, run: cd $PROJECT_DIR && ./start_kiosk.sh"
echo "5. Check the project README.md for installation instructions"
echo
echo "=== QUICK FIXES ==="
echo "Make scripts executable:"
echo "  chmod +x $PROJECT_DIR/*.sh"
echo
echo "Test Python directly:"
echo "  cd $PROJECT_DIR && python3 kiosk_browser.py"
echo
echo "Enable auto-update (run after fixing startup):"
echo "  cd $PROJECT_DIR && ./update_check.sh --setup-cron"
