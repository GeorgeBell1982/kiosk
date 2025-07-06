#!/bin/bash
# Office Kiosk Browser Installation Script for Raspberry Pi
# This script sets up the kiosk browser for automatic startup

echo "Office Kiosk Browser - Raspberry Pi Setup"
echo "========================================="
echo

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y python3-pyqt5 python3-pyqt5.qtwebengine
sudo apt install -y x11-xserver-utils unclutter

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
.venv/bin/pip install -r requirements.txt

# Make scripts executable
chmod +x start_kiosk.sh

# Set up autostart
echo "Setting up autostart..."
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/kiosk-browser.desktop << EOF
[Desktop Entry]
Type=Application
Name=Office Kiosk Browser
Exec=${PWD}/start_kiosk.sh --fullscreen
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Disable screen blanking and screensaver
echo "Configuring display settings..."
cat >> ~/.bashrc << EOF

# Disable screen blanking for kiosk
if [ "\$DISPLAY" != "" ]; then
    xset s off
    xset -dpms
    xset s noblank
fi
EOF

# Set up unclutter to hide mouse cursor
cat > ~/.config/autostart/unclutter.desktop << EOF
[Desktop Entry]
Type=Application
Name=Unclutter
Exec=unclutter -idle 1 -root
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Configure shutdown permissions for kiosk user
echo "Configuring shutdown permissions..."
echo "$USER ALL=(ALL) NOPASSWD: /sbin/shutdown" | sudo tee /etc/sudoers.d/kiosk-shutdown >/dev/null

echo
echo "Installation complete!"
echo
echo "Configuration notes:"
echo "1. Edit shortcuts directly in kiosk_browser.py if needed"
echo "2. Home Assistant URL can be changed in the shortcuts list"
echo "3. Shutdown button is available for safe Pi shutdown"
echo "4. Reboot to test automatic startup"
echo
echo "Manual start: ./start_kiosk.sh"
echo "Fullscreen:   ./start_kiosk.sh --fullscreen"
echo
echo "For autostart, the browser will launch automatically after reboot."
