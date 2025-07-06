#!/bin/bash
# Waveshare 1024x600 Touchscreen Setup for Office Kiosk Browser

echo "Waveshare 1024x600 Touchscreen Setup"
echo "===================================="
echo "This script configures your Raspberry Pi for Waveshare 1024x600 displays"
echo

# Check if we're on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "❌ This script is for Raspberry Pi only!"
    exit 1
fi

echo "=== 1. DISPLAY RESOLUTION SETUP ==="

BOOT_CONFIG="/boot/config.txt"
echo "Configuring /boot/config.txt for 1024x600 display..."

# Backup config.txt
sudo cp "$BOOT_CONFIG" "$BOOT_CONFIG.backup.$(date +%Y%m%d-%H%M%S)"
echo "✅ Backed up config.txt"

# Remove conflicting display settings
sudo sed -i '/^hdmi_mode=/d' "$BOOT_CONFIG" 2>/dev/null || true
sudo sed -i '/^hdmi_group=/d' "$BOOT_CONFIG" 2>/dev/null || true
sudo sed -i '/^hdmi_cvt/d' "$BOOT_CONFIG" 2>/dev/null || true

# Add Waveshare 1024x600 settings
cat << 'EOF' | sudo tee -a "$BOOT_CONFIG" > /dev/null

# Waveshare 1024x600 Display Configuration
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt 1024 600 60 6 0 0 0
disable_overscan=1

EOF

echo "✅ Added Waveshare 1024x600 display settings"
REBOOT_NEEDED=true

echo
echo "=== 2. TOUCHSCREEN SETUP ==="

# Enable I2C and SPI for touchscreen
echo "Enabling I2C and SPI interfaces..."

if ! grep -q "dtparam=i2c_arm=on" "$BOOT_CONFIG"; then
    echo "dtparam=i2c_arm=on" | sudo tee -a "$BOOT_CONFIG"
    echo "✅ Enabled I2C interface"
    REBOOT_NEEDED=true
fi

if ! grep -q "dtparam=spi=on" "$BOOT_CONFIG"; then
    echo "dtparam=spi=on" | sudo tee -a "$BOOT_CONFIG"
    echo "✅ Enabled SPI interface"
    REBOOT_NEEDED=true
fi

# Install touchscreen packages
echo "Installing touchscreen packages..."
sudo apt update -qq
sudo apt install -y \
    xserver-xorg-input-evdev \
    xinput-calibrator \
    libts-bin \
    evtest

echo "✅ Touchscreen packages installed"

echo
echo "=== 3. TOUCH CALIBRATION SETUP ==="

# Create calibration script
CALIB_SCRIPT="/usr/local/bin/calibrate_touch.sh"
sudo tee "$CALIB_SCRIPT" > /dev/null << 'EOF'
#!/bin/bash
# Touch calibration script for Waveshare displays

echo "Touch Calibration for Waveshare Display"
echo "======================================="
echo "Follow the on-screen instructions to calibrate your touchscreen"
echo "Touch the crosshairs as accurately as possible"
echo

# Run calibration
xinput_calibrator --list
echo
echo "Starting calibration..."
xinput_calibrator

echo
echo "Calibration completed!"
echo "If you need to run this again, use: sudo /usr/local/bin/calibrate_touch.sh"
EOF

sudo chmod +x "$CALIB_SCRIPT"
echo "✅ Created touch calibration script: $CALIB_SCRIPT"

echo
echo "=== 4. KIOSK OPTIMIZATION ==="

# Create X11 configuration for touch
X11_TOUCH_CONF="/etc/X11/xorg.conf.d/99-waveshare-touch.conf"
sudo mkdir -p /etc/X11/xorg.conf.d

sudo tee "$X11_TOUCH_CONF" > /dev/null << 'EOF'
# Waveshare touchscreen configuration
Section "InputClass"
    Identifier "Touchscreen"
    MatchIsTouchscreen "on"
    Driver "evdev"
    Option "Calibration" "0 1023 0 599"
    Option "SwapAxes" "0"
    Option "InvertX" "0"
    Option "InvertY" "0"
EndSection
EOF

echo "✅ Created X11 touchscreen configuration"

# Disable screen blanking for kiosk mode
LIGHTDM_CONF="/etc/lightdm/lightdm.conf"
if [ -f "$LIGHTDM_CONF" ]; then
    if ! grep -q "xserver-command=X -s 0 -dpms" "$LIGHTDM_CONF"; then
        sudo sed -i '/^\[Seat:\*\]/a xserver-command=X -s 0 -dpms' "$LIGHTDM_CONF"
        echo "✅ Disabled screen blanking in LightDM"
    fi
fi

echo
echo "=== 5. TESTING CURRENT SETUP ==="

echo "Current display information:"
if command -v xrandr >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
    echo "Active displays:"
    xrandr | grep " connected" | sed 's/^/  /'
    echo
    echo "Current resolution:"
    xrandr | grep "\*" | sed 's/^/  /'
else
    echo "  ⚠ X11 not running (normal if running via SSH)"
fi

echo
echo "Touch devices:"
if [ -d "/dev/input" ]; then
    ls /dev/input/event* 2>/dev/null | head -5 | sed 's/^/  /' || echo "  No event devices found"
else
    echo "  ⚠ Input devices not available"
fi

echo
echo "=== 6. CONFIGURATION SUMMARY ==="
echo "Display: 1024x600 @ 60Hz (Waveshare compatible)"
echo "Mode: HDMI Group 2, Mode 87 with custom CVT"
echo "Touch: I2C and SPI enabled"
echo "Calibration: Available via $CALIB_SCRIPT"
echo "X11 Config: Touch optimized for 1024x600"

if [ "${REBOOT_NEEDED:-false}" = "true" ]; then
    echo
    echo "🔄 REBOOT REQUIRED!"
    echo "Display and touch configuration changes require a reboot."
    echo "Would you like to reboot now? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Rebooting in 5 seconds..."
        sleep 5
        sudo reboot
    else
        echo "Please reboot manually: sudo reboot"
    fi
else
    echo
    echo "✅ Configuration complete! Test your setup:"
    echo "   cd $(dirname "$0") && ./start_kiosk.sh"
fi

echo
echo "=== POST-REBOOT STEPS ==="
echo "After rebooting:"
echo "1. Test display resolution: xrandr"
echo "2. Test touch: xinput list"
echo "3. Calibrate touch if needed: sudo $CALIB_SCRIPT"
echo "4. Start kiosk: ./start_kiosk.sh"
echo "5. If display rotation needed, add 'display_rotate=1' to $BOOT_CONFIG"

echo
echo "=== TROUBLESHOOTING ==="
echo "Common issues and solutions:"
echo "• Black screen: Check HDMI cable and power supply"
echo "• Wrong resolution: Verify hdmi_cvt line in $BOOT_CONFIG"
echo "• Touch not working: Run touch calibration script"
echo "• Inverted touch: Modify InvertX/InvertY in $X11_TOUCH_CONF"
echo "• Rotated display: Add display_rotate=1 to $BOOT_CONFIG"
