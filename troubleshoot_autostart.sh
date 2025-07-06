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

if [ -d "$AUTOSTART_DIR" ]; then
    echo "✓ Autostart directory exists: $AUTOSTART_DIR"
else
    echo "✗ Autostart directory missing: $AUTOSTART_DIR"
    echo "  Creating directory..."
    mkdir -p "$AUTOSTART_DIR"
fi

if [ -f "$KIOSK_DESKTOP" ]; then
    echo "✓ Kiosk desktop file exists: $KIOSK_DESKTOP"
    echo "  Contents:"
    cat "$KIOSK_DESKTOP" | sed 's/^/    /'
else
    echo "✗ Kiosk desktop file missing: $KIOSK_DESKTOP"
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
read -p "Would you like to recreate the autostart file? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Recreating autostart file..."
    
    cat > "$KIOSK_DESKTOP" << EOF
[Desktop Entry]
Type=Application
Name=Office Kiosk Browser
Comment=Touchscreen-friendly browser for Raspberry Pi kiosk
Exec=$START_SCRIPT
Path=$SCRIPT_DIR
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Network;WebBrowser;
EOF
    
    echo "✓ Autostart file recreated"
    echo "  File: $KIOSK_DESKTOP"
    echo "  Reboot to test autostart"
fi
