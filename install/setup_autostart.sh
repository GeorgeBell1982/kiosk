#!/bin/bash
# Setup autostart for Office Kiosk Browser on Raspberry Pi
# This script configures the app to start automatically on boot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get current directory (should be office_kiosk)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CURRENT_USER=$(whoami)

echo "Setting up Office Kiosk Browser Autostart"
echo "========================================="
echo "Project directory: $PROJECT_DIR"
echo "Current user: $CURRENT_USER"
echo

# Method 1: Desktop autostart (preferred for graphical login)
setup_desktop_autostart() {
    log "Setting up desktop autostart..."
    
    # Create autostart directory if it doesn't exist
    AUTOSTART_DIR="$HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"
    
    # Create autostart desktop file
    AUTOSTART_FILE="$AUTOSTART_DIR/office-kiosk-browser.desktop"
    
    cat > "$AUTOSTART_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Office Kiosk Browser
Comment=Auto-start Office Kiosk Browser on login
Exec=python3 $PROJECT_DIR/kiosk_browser.py --fullscreen
Path=$PROJECT_DIR
Icon=$PROJECT_DIR/icons/home.svg
Terminal=false
Categories=Network;WebBrowser;
StartupNotify=true
Hidden=false
X-GNOME-Autostart-enabled=true
EOF

    chmod +x "$AUTOSTART_FILE"
    success "Desktop autostart configured: $AUTOSTART_FILE"
}

# Method 2: Systemd user service (alternative method)
setup_systemd_user_service() {
    log "Setting up systemd user service..."
    
    # Create user systemd directory
    SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_USER_DIR"
    
    # Create user service file
    USER_SERVICE_FILE="$SYSTEMD_USER_DIR/office-kiosk-browser.service"
    
    cat > "$USER_SERVICE_FILE" << EOF
[Unit]
Description=Office Kiosk Browser (User Service)
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/%i
WorkingDirectory=$PROJECT_DIR
ExecStart=python3 $PROJECT_DIR/kiosk_browser.py --fullscreen
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

    # Enable the user service
    systemctl --user daemon-reload
    systemctl --user enable office-kiosk-browser.service
    
    success "Systemd user service configured and enabled"
}

# Method 3: Add to .bashrc for auto-launch (backup method)
setup_bashrc_autostart() {
    log "Setting up .bashrc autostart (backup method)..."
    
    # Check if we're already in .bashrc
    if ! grep -q "office_kiosk" "$HOME/.bashrc"; then
        cat >> "$HOME/.bashrc" << 'EOF'

# Auto-start Office Kiosk Browser if in graphical session
if [[ -n "$DISPLAY" || -n "$WAYLAND_DISPLAY" ]] && [[ "$XDG_SESSION_TYPE" != "tty" ]]; then
    # Check if kiosk browser is already running
    if ! pgrep -f "kiosk_browser.py" >/dev/null; then
        echo "Starting Office Kiosk Browser..."
        cd "$HOME/office_kiosk" && python3 kiosk_browser.py --fullscreen &
    fi
fi
EOF
        success ".bashrc autostart configured"
    else
        warning ".bashrc autostart already configured"
    fi
}

# Check if running on Raspberry Pi
is_raspberry_pi() {
    [[ -f /proc/cpuinfo ]] && grep -q "Raspberry Pi" /proc/cpuinfo
}

# Main setup function
main() {
    if ! is_raspberry_pi; then
        warning "Not running on Raspberry Pi - autostart setup may not work as expected"
    fi
    
    log "Configuring autostart methods..."
    
    # For kiosk mode, we want ONLY ONE method to avoid conflicts
    # Method 1: Desktop autostart (most reliable for kiosk mode)
    setup_desktop_autostart
    
    # Don't enable multiple methods simultaneously to avoid conflicts
    log "Desktop autostart configured as primary method"
    log "Other methods (systemd, bashrc) available but not enabled to prevent conflicts"
    
    echo
    success "🎉 Autostart setup complete!"
    echo
    log "The Office Kiosk Browser will now start automatically when you:"
    log "  1. Log into the desktop (desktop autostart)"
    log "  2. Start a graphical session (systemd user service)"
    log "  3. Open a terminal in graphical mode (.bashrc fallback)"
    echo
    log "To test autostart:"
    log "  1. Reboot: sudo reboot"
    log "  2. Or logout and login again"
    log "  3. Or run: systemctl --user start office-kiosk-browser.service"
    echo
    log "To disable autostart:"
    log "  rm ~/.config/autostart/office-kiosk-browser.desktop"
    log "  systemctl --user disable office-kiosk-browser.service"
    echo
}

main "$@"
