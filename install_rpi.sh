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

echo "Setup Options:"
echo "1. Standard installation"
echo "2. Fix graphics/display issues first (recommended for display problems)"
echo "3. Waveshare 1024x600 touchscreen setup"
echo "4. Exit"
echo
read -p "Choose option (1-4): " -r choice

case $choice in
    2)
        echo "Running graphics fix script..."
        chmod +x fix_pi_graphics.sh
        ./fix_pi_graphics.sh
        echo
        echo "Graphics fix completed. Continuing with installation..."
        echo
        ;;
    3)
        echo "Running Waveshare 1024x600 setup..."
        chmod +x setup_waveshare.sh
        ./setup_waveshare.sh
        echo
        echo "Waveshare setup completed. Continuing with installation..."
        echo
        ;;
    4)
        echo "Installation cancelled."
        exit 0
        ;;
    1|*)
        echo "Proceeding with standard installation..."
        ;;
esac

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y python3-pyqt5 
sudo apt install -y x11-xserver-utils unclutter

# Try to install WebEngine - package name varies by OS version
echo "Installing PyQt5 WebEngine..."
if sudo apt install -y python3-pyqt5.qtwebengine 2>/dev/null; then
    echo "Installed python3-pyqt5.qtwebengine"
elif sudo apt install -y python3-pyqt5-qtwebengine 2>/dev/null; then
    echo "Installed python3-pyqt5-qtwebengine (alternative name)"
elif sudo apt install -y python3-pyqt5.qtwebkit 2>/dev/null; then
    echo "Installed python3-pyqt5.qtwebkit (fallback for older systems)"
    echo "Warning: Using QtWebKit instead of QtWebEngine"
else
    echo "Warning: Could not install PyQt5 WebEngine via apt"
    echo "Will try to install via pip in virtual environment"
    WEBENGINE_FALLBACK=true
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment with system packages..."
    # Create venv with access to system site packages for PyQt5
    python3 -m venv --system-site-packages .venv
fi

# Install Python dependencies (will skip PyQt5 if already available via system packages)
echo "Installing Python dependencies..."
# Use Raspberry Pi specific requirements that don't include PyQt5
if [ -f "requirements-rpi.txt" ]; then
    echo "Using Raspberry Pi specific requirements..."
    .venv/bin/pip install -r requirements-rpi.txt
else
    echo "Fallback to standard requirements (may fail on PyQt5)..."
    .venv/bin/pip install -r requirements.txt || {
        echo "Some packages failed to install via pip, but that's OK if system packages are available"
    }
fi

# If WebEngine system package failed, try pip installation
if [ "$WEBENGINE_FALLBACK" = "true" ]; then
    echo "Attempting to install PyQtWebEngine via pip..."
    .venv/bin/pip install PyQtWebEngine || {
        echo "Failed to install PyQtWebEngine via pip"
        echo "The application may not work properly without WebEngine"
    }
fi

# Verify PyQt5 is available
echo "Verifying PyQt5 installation..."
.venv/bin/python -c "import PyQt5; print('PyQt5 is available')" || {
    echo "Error: PyQt5 not found. Please ensure system packages are installed:"
    echo "sudo apt install python3-pyqt5"
    exit 1
}

# Try to verify WebEngine (but don't fail if not available)
echo "Verifying WebEngine installation..."
.venv/bin/python -c "import PyQt5.QtWebEngineWidgets; print('QtWebEngine is available')" || {
    echo "Warning: QtWebEngine not available. Trying QtWebKit as fallback..."
    .venv/bin/python -c "import PyQt5.QtWebKit; print('QtWebKit is available as fallback')" || {
        echo "Warning: Neither QtWebEngine nor QtWebKit is available"
        echo "The browser functionality may be limited"
    }
}

# Make scripts executable
chmod +x start_kiosk.sh
chmod +x update_check.sh

# Create update log file with proper permissions
sudo touch /var/log/kiosk-update.log
sudo chown $USER:$USER /var/log/kiosk-update.log

# Set up autostart
echo "Setting up autostart..."

# Ask user which autostart method to use
echo "Choose autostart method:"
echo "1. Modern XDG autostart (recommended for newer Pi OS)"
echo "2. Legacy LXDE autostart (for older Pi OS versions)"
echo "3. Both XDG and systemd user service (most reliable)"
echo

read -p "Choose option (1-3) [default: 3]: " -r autostart_choice
autostart_choice=${autostart_choice:-3}

case $autostart_choice in
    1)
        echo "Setting up XDG autostart..."
        mkdir -p ~/.config/autostart

        cat > ~/.config/autostart/kiosk-browser.desktop << EOF
[Desktop Entry]
Type=Application
Name=Office Kiosk Browser
Comment=Touchscreen-friendly browser for Raspberry Pi kiosk
Exec=${PWD}/start_kiosk.sh
Path=${PWD}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Network;WebBrowser;
EOF
        echo "✓ XDG autostart configured"
        ;;
        
    2)
        echo "Setting up legacy LXDE autostart..."
        LXDE_AUTOSTART_DIR="$HOME/.config/lxsession/LXDE-pi"
        LXDE_AUTOSTART_FILE="$LXDE_AUTOSTART_DIR/autostart"
        
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
            echo "@sh -c 'sleep 10 && cd ${PWD} && ${PWD}/start_kiosk.sh'" >> "$LXDE_AUTOSTART_FILE"
        fi
        echo "✓ Legacy LXDE autostart configured"
        ;;
        
    3)
        echo "Setting up dual autostart (XDG + systemd)..."
        mkdir -p ~/.config/autostart

        cat > ~/.config/autostart/kiosk-browser.desktop << EOF
[Desktop Entry]
Type=Application
Name=Office Kiosk Browser
Comment=Touchscreen-friendly browser for Raspberry Pi kiosk
Exec=${PWD}/start_kiosk.sh
Path=${PWD}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Network;WebBrowser;
EOF

        # Also set up systemd user service as backup
        echo "Setting up systemd user service..."
        mkdir -p ~/.config/systemd/user

        cat > ~/.config/systemd/user/kiosk-browser.service << EOF
[Unit]
Description=Office Kiosk Browser
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/$UID
WorkingDirectory=${PWD}
ExecStart=${PWD}/start_kiosk.sh
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

        # Enable systemd user service
        systemctl --user daemon-reload
        systemctl --user enable kiosk-browser.service

        echo "✓ Dual autostart configured (XDG + systemd)"
        ;;
        
    *)
        echo "Invalid option, using default (dual autostart)..."
        # Set up dual autostart (XDG + systemd)
        mkdir -p ~/.config/autostart

        cat > ~/.config/autostart/kiosk-browser.desktop << EOF
[Desktop Entry]
Type=Application
Name=Office Kiosk Browser
Comment=Touchscreen-friendly browser for Raspberry Pi kiosk
Exec=${PWD}/start_kiosk.sh
Path=${PWD}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Network;WebBrowser;
EOF

        # Also set up systemd user service as backup
        echo "Setting up systemd user service..."
        mkdir -p ~/.config/systemd/user

        cat > ~/.config/systemd/user/kiosk-browser.service << EOF
[Unit]
Description=Office Kiosk Browser
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/$UID
WorkingDirectory=${PWD}
ExecStart=${PWD}/start_kiosk.sh
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

        # Enable systemd user service
        systemctl --user daemon-reload
        systemctl --user enable kiosk-browser.service

        echo "✓ Dual autostart configured (XDG + systemd)"
        ;;
esac

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
echo "4. Autostart is configured - reboot to test"
echo
echo "Manual start: ./start_kiosk.sh"
echo "Fullscreen:   ./start_kiosk.sh --fullscreen"
echo
echo "Autostart troubleshooting:"
echo "- Run: ./troubleshoot_autostart.sh"
echo "- Check logs: journalctl --user -u kiosk-browser.service"
echo "- Manual test: gtk-launch kiosk-browser.desktop"
echo
echo "Important: Ensure Pi boots to desktop (not console)"
echo "Use: sudo raspi-config -> Boot Options -> Desktop/CLI -> Desktop Autologin"
echo
echo "For autostart, the browser will launch automatically after reboot."
