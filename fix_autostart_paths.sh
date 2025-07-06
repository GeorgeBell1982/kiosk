#!/bin/bash
# Fix existing autostart files with wrong paths

echo "Office Kiosk Browser - Fix Autostart Paths"
echo "=========================================="
echo

# Get the correct paths
SCRIPT_DIR_ABS="$(cd "$(dirname "$0")" && pwd)"
START_SCRIPT_ABS="$SCRIPT_DIR_ABS/start_kiosk.sh"

echo "Correct paths:"
echo "  Script directory: $SCRIPT_DIR_ABS"
echo "  Start script: $START_SCRIPT_ABS"
echo

# Check if start script exists
if [ ! -f "$START_SCRIPT_ABS" ]; then
    echo "❌ Start script not found: $START_SCRIPT_ABS"
    exit 1
fi

# Make sure start script is executable
chmod +x "$START_SCRIPT_ABS"
echo "✓ Made start script executable"

# Fix XDG autostart file
AUTOSTART_DIR="$HOME/.config/autostart"
KIOSK_DESKTOP="$AUTOSTART_DIR/kiosk-browser.desktop"

if [ -f "$KIOSK_DESKTOP" ]; then
    echo
    echo "=== FIXING XDG AUTOSTART FILE ==="
    echo "Found existing autostart file: $KIOSK_DESKTOP"
    
    # Show current content
    echo "Current content:"
    cat "$KIOSK_DESKTOP" | sed 's/^/  /'
    echo
    
    # Check if it has wrong paths
    if grep -q "/path/to/office_kiosk" "$KIOSK_DESKTOP" || ! grep -q "$SCRIPT_DIR_ABS" "$KIOSK_DESKTOP"; then
        echo "❌ Found incorrect paths. Fixing..."
        
        # Create corrected desktop file
        cat > "$KIOSK_DESKTOP" << EOF
[Desktop Entry]
Type=Application
Name=Office Kiosk Browser
Comment=Touchscreen-friendly browser for Raspberry Pi kiosk
Exec=$START_SCRIPT_ABS
Path=$SCRIPT_DIR_ABS
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Network;WebBrowser;
EOF
        
        echo "✓ Fixed XDG autostart file"
        echo "New content:"
        cat "$KIOSK_DESKTOP" | sed 's/^/  /'
    else
        echo "✅ XDG autostart file already has correct paths"
    fi
else
    echo
    echo "=== CREATING XDG AUTOSTART FILE ==="
    mkdir -p "$AUTOSTART_DIR"
    
    cat > "$KIOSK_DESKTOP" << EOF
[Desktop Entry]
Type=Application
Name=Office Kiosk Browser
Comment=Touchscreen-friendly browser for Raspberry Pi kiosk
Exec=$START_SCRIPT_ABS
Path=$SCRIPT_DIR_ABS
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Network;WebBrowser;
EOF
    
    echo "✓ Created XDG autostart file: $KIOSK_DESKTOP"
fi

# Fix LXDE autostart file
LXDE_AUTOSTART_DIR="$HOME/.config/lxsession/LXDE-pi"
LXDE_AUTOSTART_FILE="$LXDE_AUTOSTART_DIR/autostart"

if [ -f "$LXDE_AUTOSTART_FILE" ]; then
    echo
    echo "=== FIXING LXDE AUTOSTART FILE ==="
    echo "Found existing LXDE autostart file: $LXDE_AUTOSTART_FILE"
    
    # Show current content
    echo "Current content:"
    cat "$LXDE_AUTOSTART_FILE" | sed 's/^/  /'
    echo
    
    # Check if it has wrong paths
    if grep -q "/path/to/office_kiosk" "$LXDE_AUTOSTART_FILE"; then
        echo "❌ Found incorrect paths. Fixing..."
        
        # Replace wrong paths with correct ones
        sed -i "s|/path/to/office_kiosk|$SCRIPT_DIR_ABS|g" "$LXDE_AUTOSTART_FILE"
        
        echo "✓ Fixed LXDE autostart file"
        echo "New content:"
        cat "$LXDE_AUTOSTART_FILE" | sed 's/^/  /'
    else
        echo "✅ LXDE autostart file paths look correct"
    fi
fi

# Check systemd user services
echo
echo "=== CHECKING SYSTEMD SERVICES ==="

# Check user service
USER_SERVICE="$HOME/.config/systemd/user/kiosk-browser.service"
if [ -f "$USER_SERVICE" ]; then
    echo "Found user service: $USER_SERVICE"
    
    if grep -q "/path/to/office_kiosk" "$USER_SERVICE"; then
        echo "❌ Found incorrect paths in user service. Fixing..."
        sed -i "s|/path/to/office_kiosk|$SCRIPT_DIR_ABS|g" "$USER_SERVICE"
        
        # Reload systemd daemon
        systemctl --user daemon-reload
        echo "✓ Fixed user service and reloaded daemon"
    else
        echo "✅ User service paths look correct"
    fi
fi

# Check system service
SYSTEM_SERVICE="/etc/systemd/system/kiosk-browser.service"
if [ -f "$SYSTEM_SERVICE" ]; then
    echo "Found system service: $SYSTEM_SERVICE"
    
    if sudo grep -q "/path/to/office_kiosk" "$SYSTEM_SERVICE" 2>/dev/null; then
        echo "❌ Found incorrect paths in system service. Fixing..."
        sudo sed -i "s|/path/to/office_kiosk|$SCRIPT_DIR_ABS|g" "$SYSTEM_SERVICE"
        
        # Reload systemd daemon
        sudo systemctl daemon-reload
        echo "✓ Fixed system service and reloaded daemon"
    else
        echo "✅ System service paths look correct"
    fi
fi

echo
echo "=== PATH FIX SUMMARY ==="
echo "✓ Script directory: $SCRIPT_DIR_ABS"
echo "✓ Start script: $START_SCRIPT_ABS"
echo "✓ All autostart files checked and fixed if needed"
echo
echo "=== TESTING ==="
echo "Testing if start script can be executed:"
if "$START_SCRIPT_ABS" --help >/dev/null 2>&1; then
    echo "✅ Start script test successful"
else
    echo "❌ Start script test failed"
    echo "Try running manually: $START_SCRIPT_ABS"
fi

echo
echo "=== NEXT STEPS ==="
echo "1. Reboot to test autostart: sudo reboot"
echo "2. Check logs after reboot: journalctl --user -f"
echo "3. Manual test: $START_SCRIPT_ABS"
echo "4. If still issues, run: ./debug_startup.sh"
