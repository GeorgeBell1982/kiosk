#!/bin/bash
# Fix Raspberry Pi graphics and display issues for Office Kiosk Browser

echo "Raspberry Pi Graphics & Display Fix"
echo "=================================="
echo "This script fixes common issues:"
echo "- libEGL warnings and DRI2 authentication errors"
echo "- QtWebEngine falling back to QtWebKit"
echo "- Fullscreen not working properly"
echo "- Missing icons and graphics"
echo

# Check if we're on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "❌ This script is for Raspberry Pi only!"
    exit 1
fi

echo "=== 1. CHECKING CURRENT GPU MEMORY ==="
GPU_MEMORY=$(vcgencmd get_mem gpu | cut -d= -f2 | cut -dM -f1)
echo "Current GPU memory: ${GPU_MEMORY}MB"

if [ "$GPU_MEMORY" -lt 64 ]; then
    echo "⚠ GPU memory is too low! Need at least 64MB for graphics."
    echo "Would you like to increase GPU memory to 64MB? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Adding gpu_mem=64 to /boot/config.txt..."
        if ! grep -q "gpu_mem=" /boot/config.txt; then
            echo "gpu_mem=64" | sudo tee -a /boot/config.txt
            echo "✅ GPU memory setting added"
        else
            sudo sed -i 's/gpu_mem=.*/gpu_mem=64/' /boot/config.txt
            echo "✅ GPU memory setting updated"
        fi
        REBOOT_NEEDED=true
    fi
else
    echo "✅ GPU memory is adequate (${GPU_MEMORY}MB)"
fi

echo
echo "=== 2. CHECKING GRAPHICS DRIVERS ==="

# Check for VC4 driver
if lsmod | grep -q vc4; then
    echo "✅ VC4 graphics driver is loaded"
else
    echo "⚠ VC4 graphics driver not loaded"
    echo "Enabling VC4 driver in /boot/config.txt..."
    
    if ! grep -q "dtoverlay=vc4-kms-v3d" /boot/config.txt; then
        echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt
        echo "✅ VC4 driver enabled"
        REBOOT_NEEDED=true
    fi
fi

echo
echo "=== 3. INSTALLING REQUIRED PACKAGES ==="

echo "Updating package list..."
sudo apt update -qq

echo "Installing/updating graphics packages..."
sudo apt install -y \
    python3-pyqt5 \
    python3-pyqt5.qtwebengine \
    python3-pyqt5.qtwebkit \
    libgl1-mesa-dri \
    mesa-utils \
    xserver-xorg-video-fbdev \
    xserver-xorg-video-vesa

echo "Installing additional dependencies..."
sudo apt install -y \
    libqt5webkit5-dev \
    qtwebengine5-dev \
    chromium-browser \
    fonts-liberation

echo
echo "=== 4. CONFIGURING CHROMIUM FLAGS ==="

# Create chromium flags for better WebEngine support
CHROMIUM_FLAGS="/etc/chromium-browser/default"
if [ ! -f "$CHROMIUM_FLAGS" ]; then
    sudo mkdir -p /etc/chromium-browser
    sudo touch "$CHROMIUM_FLAGS"
fi

echo "Adding Chromium flags for better performance..."
sudo tee "$CHROMIUM_FLAGS" > /dev/null << 'EOF'
# Chromium flags for Raspberry Pi kiosk
CHROMIUM_FLAGS="--disable-gpu-sandbox --disable-software-rasterizer --enable-gpu-rasterization --ignore-gpu-blacklist --disable-dev-shm-usage --disable-web-security --allow-running-insecure-content --no-sandbox"
EOF

echo
echo "=== 5. SETTING UP DISPLAY CONFIGURATION ==="

# Check boot config for proper display settings
echo "Checking display configuration..."
echo "Using generic display configuration"

# Basic display settings that work with most displays
BOOT_CONFIG="/boot/config.txt"

# Ensure HDMI is enabled
if ! grep -q "hdmi_force_hotplug=1" "$BOOT_CONFIG"; then
    echo "hdmi_force_hotplug=1" | sudo tee -a "$BOOT_CONFIG"
    echo "✅ Added HDMI hotplug setting"
    REBOOT_NEEDED=true
fi

# Disable overscan for better display
if ! grep -q "disable_overscan=1" "$BOOT_CONFIG"; then
    echo "disable_overscan=1" | sudo tee -a "$BOOT_CONFIG"
    echo "✅ Disabled overscan for better display"
    REBOOT_NEEDED=true
fi

echo "✅ Basic display configuration completed"

echo
echo "=== 6. TESTING GRAPHICS ==="

echo "Testing OpenGL..."
if command -v glxinfo >/dev/null 2>&1; then
    GL_RENDERER=$(glxinfo | grep "OpenGL renderer" | cut -d: -f2 | xargs)
    echo "OpenGL Renderer: $GL_RENDERER"
    
    if echo "$GL_RENDERER" | grep -q "VC4"; then
        echo "✅ Hardware acceleration is working"
    else
        echo "⚠ Software rendering detected"
    fi
else
    echo "⚠ glxinfo not available"
fi

echo
echo "Testing Qt WebEngine availability..."
cd "$(dirname "$0")" || exit 1
if python3 -c "from PyQt5.QtWebEngineWidgets import QWebEngineView; print('✅ QtWebEngine is available')" 2>/dev/null; then
    echo "✅ QtWebEngine working properly"
else
    echo "⚠ QtWebEngine not working, will fall back to QtWebKit"
    echo "  This is normal for older Raspberry Pi or limited GPU memory"
fi

echo
echo "=== 7. CONFIGURATION SUMMARY ==="
echo "GPU Memory: ${GPU_MEMORY}MB"
echo "VC4 Driver: $(lsmod | grep -q vc4 && echo "Enabled" || echo "Disabled")"
echo "QtWebEngine: $(python3 -c "from PyQt5.QtWebEngineWidgets import QWebEngineView" 2>/dev/null && echo "Available" || echo "Not Available")"
echo "QtWebKit: $(python3 -c "from PyQt5.QtWebKitWidgets import QWebView" 2>/dev/null && echo "Available" || echo "Not Available")"

echo
echo "=== RECOMMENDATIONS ==="
echo "1. ✅ Install packages completed"
echo "2. ✅ GPU memory configuration checked"
echo "3. ✅ Graphics drivers configured"

if [ "${REBOOT_NEEDED:-false}" = "true" ]; then
    echo
    echo "🔄 REBOOT REQUIRED!"
    echo "Configuration changes require a reboot to take effect."
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
    echo "✅ No reboot required. You can test the kiosk now:"
    echo "   cd $(pwd) && ./start_kiosk.sh"
fi

echo
echo "=== TROUBLESHOOTING ==="
echo "If issues persist:"
echo "1. Check logs: tail -f ~/.local/share/Office_Kiosk_Browser/logs/"
echo "2. Run debug script: ./debug_startup.sh"
echo "3. Manually test Qt: python3 -c 'from PyQt5.QtWidgets import QApplication'"
echo "4. Check display: echo \$DISPLAY && xset q"
echo "5. For touchscreen: Enable SPI and I2C in raspi-config"
