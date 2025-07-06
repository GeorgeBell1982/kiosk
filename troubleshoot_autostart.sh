#!/bin/bash
# Troubleshoot autostart issues for Office Kiosk Browser

echo "Office Kiosk Browser - Autostart Troubleshooting"
echo "================================================"
echo

# Check if we're on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This appears to not be a Raspberry Pi"
    echo "Autostart troubleshooting is designed for Raspberry Pi"
    echo
fi

# Check current desktop environment
echo "Desktop Environment Detection:"
if [ "$XDG_CURRENT_DESKTOP" ]; then
    echo "  Current Desktop: $XDG_CURRENT_DESKTOP"
else
    echo "  Desktop environment not detected"
fi

if [ "$DESKTOP_SESSION" ]; then
    echo "  Desktop Session: $DESKTOP_SESSION"
fi
echo

# Check autostart directory and files
echo "Autostart Configuration:"
AUTOSTART_DIR="$HOME/.config/autostart"
KIOSK_DESKTOP="$AUTOSTART_DIR/kiosk-browser.desktop"

# Check for LXDE-pi autostart (legacy method)
LXDE_AUTOSTART_DIR="$HOME/.config/lxsession/LXDE-pi"
LXDE_AUTOSTART="$LXDE_AUTOSTART_DIR/autostart"

echo "Checking autostart methods:"

# XDG autostart method
if [ -d "$AUTOSTART_DIR" ]; then
    echo "✓ XDG autostart directory exists: $AUTOSTART_DIR"
else
    echo "✗ XDG autostart directory missing: $AUTOSTART_DIR"
    echo "  Creating directory..."
    mkdir -p "$AUTOSTART_DIR"
fi

if [ -f "$KIOSK_DESKTOP" ]; then
    echo "✓ XDG desktop file exists: $KIOSK_DESKTOP"
    echo "  Contents:"
    cat "$KIOSK_DESKTOP" | sed 's/^/    /'
else
    echo "✗ XDG desktop file missing: $KIOSK_DESKTOP"
fi

# LXDE-pi autostart method (legacy)
if [ -d "$LXDE_AUTOSTART_DIR" ]; then
    echo "✓ LXDE-pi autostart directory exists: $LXDE_AUTOSTART_DIR"
    if [ -f "$LXDE_AUTOSTART" ]; then
        echo "✓ LXDE-pi autostart file exists: $LXDE_AUTOSTART"
        echo "  Contents:"
        cat "$LXDE_AUTOSTART" | sed 's/^/    /'
        
        # Check if our kiosk is already in the LXDE autostart
        if grep -q "kiosk" "$LXDE_AUTOSTART" 2>/dev/null; then
            echo "✓ Kiosk browser found in LXDE autostart"
        else
            echo "✗ Kiosk browser not found in LXDE autostart"
        fi
    else
        echo "✗ LXDE-pi autostart file missing: $LXDE_AUTOSTART"
    fi
else
    echo "✗ LXDE-pi autostart directory missing: $LXDE_AUTOSTART_DIR"
    echo "  This is normal if not using LXDE-pi desktop environment"
fi
echo

# Check if the start script exists and is executable
SCRIPT_DIR="$(dirname "$0")"
START_SCRIPT="$SCRIPT_DIR/start_kiosk.sh"

echo "Start Script Check:"
if [ -f "$START_SCRIPT" ]; then
    echo "✓ Start script exists: $START_SCRIPT"
    if [ -x "$START_SCRIPT" ]; then
        echo "✓ Start script is executable"
    else
        echo "✗ Start script is not executable"
        echo "  Fixing permissions..."
        chmod +x "$START_SCRIPT"
    fi
else
    echo "✗ Start script missing: $START_SCRIPT"
fi
echo

# Check display environment
echo "Display Environment:"
if [ "$DISPLAY" ]; then
    echo "✓ DISPLAY is set: $DISPLAY"
else
    echo "✗ DISPLAY is not set (this is normal if running via SSH)"
fi

if command -v xset >/dev/null 2>&1; then
    echo "✓ xset command available"
else
    echo "✗ xset command not found"
    echo "  Install with: sudo apt install x11-xserver-utils"
fi
echo

# Check for common autostart issues
echo "Common Autostart Issues:"

# Check if running in console mode
if [ "$TERM" = "linux" ] && [ -z "$DISPLAY" ]; then
    echo "⚠ Running in console mode - GUI autostart won't work"
    echo "  Ensure Pi boots to desktop, not console"
    echo "  Use: sudo raspi-config -> Boot Options -> Desktop/CLI -> Desktop Autologin"
fi

# Check systemd user session
if systemctl --user is-active --quiet default.target 2>/dev/null; then
    echo "✓ User systemd session is running"
else
    echo "⚠ User systemd session may not be running"
fi

# Check for LXDE-pi autostart (legacy method)
LXDE_AUTOSTART_DIR="$HOME/.config/lxsession/LXDE-pi"
LXDE_AUTOSTART_FILE="$LXDE_AUTOSTART_DIR/autostart"

echo "LXDE Autostart Check (Legacy Method):"
if [ -d "$LXDE_AUTOSTART_DIR" ]; then
    echo "✓ LXDE-pi directory exists: $LXDE_AUTOSTART_DIR"
    if [ -f "$LXDE_AUTOSTART_FILE" ]; then
        echo "✓ LXDE autostart file exists: $LXDE_AUTOSTART_FILE"
        if grep -q "kiosk" "$LXDE_AUTOSTART_FILE" 2>/dev/null; then
            echo "✓ Kiosk entry found in LXDE autostart"
            echo "  Kiosk entries:"
            grep "kiosk" "$LXDE_AUTOSTART_FILE" | sed 's/^/    /'
        else
            echo "✗ No kiosk entry found in LXDE autostart"
        fi
    else
        echo "✗ LXDE autostart file missing: $LXDE_AUTOSTART_FILE"
    fi
else
    echo "✗ LXDE-pi directory not found: $LXDE_AUTOSTART_DIR"
    echo "  This is normal for newer Raspberry Pi OS versions"
fi
echo

# Check for conflicting desktop files
CONFLICTING_FILES=(
    "$HOME/.config/autostart/chromium-browser.desktop"
    "$HOME/.config/autostart/office-kiosk.desktop"
    "$HOME/.config/autostart/browser.desktop"
)

for file in "${CONFLICTING_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "⚠ Found potentially conflicting autostart file: $file"
    fi
done
echo

# Test the application manually
echo "Manual Test:"
echo "Testing if the application can start..."
cd "$SCRIPT_DIR"
if ./start_kiosk.sh --help >/dev/null 2>&1; then
    echo "✓ Application can be started manually"
else
    echo "✗ Application fails to start manually"
    echo "  This needs to be fixed before autostart will work"
fi
echo

# Provide solutions
echo "Recommended Actions:"
echo "1. Ensure Raspberry Pi boots to desktop (not console)"
echo "   sudo raspi-config -> Boot Options -> Desktop/CLI -> Desktop Autologin"
echo
echo "2. If still not working, try creating systemd service instead:"
echo "   sudo systemctl --user enable kiosk-browser.service"
echo
echo "3. Test manual startup first:"
echo "   cd $(pwd) && ./start_kiosk.sh"
echo
echo "4. Check logs after reboot:"
echo "   journalctl --user -u kiosk-browser.service"
echo
echo "5. For immediate testing without reboot:"
echo "   You can run the desktop file manually:"
echo "   gtk-launch kiosk-browser.desktop"
echo

# Offer to recreate autostart file
echo "Setup Options:"
echo "1. Recreate XDG autostart file (recommended for newer Pi OS)"
echo "2. Set up legacy LXDE autostart (for older Pi OS versions)"
echo "3. Exit without changes"
echo

read -p "Choose an option (1-3): " -r choice

case $choice in
    1)
        echo "Recreating XDG autostart file..."
        
        # Get absolute paths
        SCRIPT_DIR_ABS="$(cd "$(dirname "$0")" && pwd)"
        START_SCRIPT_ABS="$SCRIPT_DIR_ABS/start_kiosk.sh"
        
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
        
        echo "✓ XDG autostart file recreated"
        echo "  File: $KIOSK_DESKTOP"
        echo "  Exec: $START_SCRIPT_ABS"
        echo "  Path: $SCRIPT_DIR_ABS"
        echo "  Reboot to test autostart"
        ;;
    
    2)
        echo "Setting up legacy LXDE autostart..."
        
        # Get absolute paths
        SCRIPT_DIR_ABS="$(cd "$(dirname "$0")" && pwd)"
        START_SCRIPT_ABS="$SCRIPT_DIR_ABS/start_kiosk.sh"
        
        # Create LXDE autostart directory if it doesn't exist
        mkdir -p "$LXDE_AUTOSTART_DIR"
        
        # Create or update the LXDE autostart file
        if [ ! -f "$LXDE_AUTOSTART_FILE" ]; then
            # Create new file with default LXDE entries
            cat > "$LXDE_AUTOSTART_FILE" << EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
EOF
        fi
        
        # Add kiosk entry if not already present
        if ! grep -q "kiosk" "$LXDE_AUTOSTART_FILE" 2>/dev/null; then
            echo "@sh -c 'sleep 10 && cd $SCRIPT_DIR_ABS && $START_SCRIPT_ABS'" >> "$LXDE_AUTOSTART_FILE"
            echo "✓ Added kiosk entry to LXDE autostart"
            echo "  Command: cd $SCRIPT_DIR_ABS && $START_SCRIPT_ABS"
        else
            echo "⚠ Kiosk entry already exists in LXDE autostart"
        fi
        
        # Add onboard (on-screen keyboard) as the last entry if not already present
        if ! grep -q "@onboard" "$LXDE_AUTOSTART_FILE" 2>/dev/null; then
            echo "@onboard" >> "$LXDE_AUTOSTART_FILE"
            echo "✓ Added onboard (on-screen keyboard) to LXDE autostart"
        else
            echo "⚠ Onboard entry already exists in LXDE autostart"
        fi
        
        echo "✓ Legacy LXDE autostart configured"
        echo "  File: $LXDE_AUTOSTART_FILE"
        echo "  Note: This method works best with older Raspberry Pi OS versions"
        echo "  Reboot to test autostart"
        ;;
    
    3)
        echo "No changes made."
        ;;
    
    *)
        echo "Invalid option. No changes made."
        ;;
esac
