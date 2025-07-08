# Office Kiosk Browser - Complete Guide

A modern, touchscreen-friendly web browser application built with PyQt6, designed specifically for Raspberry Pi kiosk installations but also works on Windows for development.

## Quick Start

### Raspberry Pi Installation (Recommended)
```bash
# Clone the repository
git clone <repository-url> office_kiosk
cd office_kiosk

# Run the automated installer
./install/quick_install_pyqt6.sh

# Start the application
python3 kiosk_browser.py
```

### Manual Installation
```bash
# For Raspberry Pi (Bookworm+)
sudo apt update
sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6.qtsvg python3-pyqt6-dev wvkbd

# For other systems
pip3 install PyQt6 PyQt6-WebEngine PyQt6-Svg
```

## Features

### 🖥️ **Modern Web Browser**
- **Qt6 WebEngine**: Full modern web compatibility
- **YouTube & Social Media**: Works with modern web standards
- **Responsive Design**: Optimized for 1024x600 touchscreens
- **Home Assistant Integration**: Direct shortcuts to HA dashboard

### 🖱️ **Touchscreen Optimized**
- **Large Touch Targets**: All buttons sized for finger interaction
- **Virtual Keyboard**: Integrated wvkbd support for text input
- **Gesture Support**: Touch-friendly navigation
- **Fullscreen Mode**: Distraction-free kiosk experience

### 🎛️ **Control Panel**
**Navigation Controls:**
- Back, Forward, Refresh, Home buttons
- Fullscreen toggle
- Virtual keyboard toggle (Pi only)
- System shutdown (Pi only)

**Quick Shortcuts:**
- Home Assistant dashboard
- YouTube Music
- Google Search
- YouTube

### 🔧 **System Integration**
- **Systemd Service**: Auto-start on boot
- **Desktop Integration**: Appears in application menu
- **Config Management**: Persistent settings
- **Auto-updates**: Built-in update checking

## Hardware Support

### ✅ **Tested Platforms**
- **Raspberry Pi 4/5**: Primary target platform
- **Raspberry Pi 3B+**: Supported with reduced performance
- **Windows 10/11**: Development and testing
- **Linux Desktop**: General compatibility

### 📺 **Display Compatibility**
- **Waveshare Touchscreens**: 1024x600, 800x480
- **Official Pi Touchscreen**: 800x480
- **HDMI Displays**: Any resolution
- **Multi-monitor**: Automatic detection

## Installation Methods

### 🚀 **Method 1: Quick Install (Recommended)**
```bash
./install/quick_install_pyqt6.sh
```
- Automatically detects Pi model and OS version
- Installs all dependencies including virtual keyboard
- Tests installation and provides verification
- Handles system updates automatically

### 🔧 **Method 2: Manual Installation**
```bash
# Install Qt6 packages
sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6.qtsvg

# Install virtual keyboard
sudo apt install wvkbd

# Install build tools (if needed)
sudo apt install build-essential python3-dev
```

### 🛠️ **Method 3: Source Build**
For older systems or custom configurations:
```bash
./install/build_pyqt6_rpi.sh
```

## Configuration

### 📋 **Basic Setup**
Edit `config.ini`:
```ini
[DEFAULT]
home_url = http://homeassistant.local:8123
fullscreen_on_pi = true
enable_developer_tools = false

[SHORTCUTS]
homeassistant_url = http://homeassistant.local:8123
youtube_music_url = https://music.youtube.com
google_url = https://www.google.com
youtube_url = https://www.youtube.com
```

### 🎯 **Auto-start Configuration**
```bash
# Install systemd service
sudo cp systemd/kiosk-browser.service /etc/systemd/system/
sudo systemctl enable kiosk-browser.service
sudo systemctl start kiosk-browser.service
```

### ⌨️ **Virtual Keyboard Setup**
The virtual keyboard (wvkbd) is automatically configured for:
- Landscape layout optimized for touchscreens
- 250px height for good visibility
- Automatic positioning at bottom of screen
- Toggle button in control panel (Pi only)

## Testing & Troubleshooting

### 🧪 **Testing Commands**
```bash
# Test Qt6 installation
python3 tests/test_qt_version.py

# Test SVG icon support
python3 tests/test_svg_icons.py

# Test basic functionality
python3 kiosk_browser.py
```

### 🔍 **Troubleshooting**
```bash
# Run comprehensive diagnostics
./install/troubleshoot_pyqt6.sh

# Check system compatibility
./install/troubleshoot_pyqt6.sh info

# Auto-fix common issues
./install/troubleshoot_pyqt6.sh fix
```

### 📝 **Common Issues**

**Qt6 WebEngine not working:**
- Ensure you're running Pi OS Bookworm or newer
- Install missing packages: `sudo apt install python3-pyqt6.qtwebengine`
- Check GPU memory: Add `gpu_mem=64` to `/boot/config.txt`

**SVG icons not displaying:**
- Install SVG support: `sudo apt install python3-pyqt6.qtsvg`
- Fallback text icons will be used if SVG unavailable

**Virtual keyboard not working:**
- Install wvkbd: `sudo apt install wvkbd`
- Check display manager (Wayland preferred)
- Button shows installation instructions if not available

**Touchscreen not responding:**
- Check display drivers are installed
- Verify touch input: `evtest` or `xinput list`
- Some displays need specific drivers

## Development

### 🏗️ **Project Structure**
```
office_kiosk/
├── kiosk_browser.py          # Main application
├── version.py                # Version management
├── config.ini                # Configuration file
├── requirements.txt          # Python dependencies
├── icons/                    # SVG icon assets
├── install/                  # Installation scripts
│   ├── quick_install_pyqt6.sh
│   ├── build_pyqt6_rpi.sh
│   └── troubleshoot_pyqt6.sh
├── tests/                    # Test scripts
├── scripts/                  # Utility scripts
├── systemd/                  # Service files
└── docs/                     # Documentation
```

### 🔄 **Development Workflow**
1. **Test on Windows**: Fast development cycle
2. **Test on Pi**: Hardware validation
3. **Create installer**: Package for distribution
4. **Document changes**: Update this guide

### 📦 **Building Releases**
```bash
# Update version
python3 -c "from version import update_version; update_version('1.x.x')"

# Test installation
./install/quick_install_pyqt6.sh

# Create git tag
git tag -a v1.x.x -m "Release version 1.x.x"
git push origin v1.x.x
```

## Migration Notes

### 🔄 **Qt5 → Qt6 Migration**
This project has been fully migrated from Qt5 to Qt6 for better modern web compatibility:

**✅ Benefits:**
- Better JavaScript and CSS support
- Improved security and performance
- Modern web standards compatibility
- Better touch input handling

**⚠️ Changes:**
- Requires Pi OS Bookworm or newer
- Different installation packages
- SVG support requires separate module
- Some Qt5 methods deprecated

**📦 Legacy Support:**
- Qt5 backup preserved in `kiosk_browser_qt5_backup.py`
- Migration guide available for reference
- Can fallback to Qt5 on older systems if needed

## License & Credits

**License**: MIT License (see LICENSE file)

**Credits:**
- Built with PyQt6 and Qt WebEngine
- Icons designed for touchscreen use
- Virtual keyboard integration via wvkbd
- Optimized for Raspberry Pi hardware

**Contributing:**
1. Fork the repository
2. Create feature branch
3. Test on both Windows and Pi
4. Submit pull request with tests

---

For more specific guides, see the `docs/` directory:
- Installation troubleshooting
- Hardware-specific setup guides  
- Advanced configuration options
- Development guidelines
