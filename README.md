# Office Kiosk Browser

A modern, touchscreen-friendly web browser built with PyQt6, designed for Raspberry Pi kiosk installations.

## 🚀 Quick Start

### Raspberry Pi (Recommended)
```bash
git clone <repository-url> office_kiosk
cd office_kiosk
./install/quick_install_pyqt6.sh
python3 kiosk_browser.py
```

### Other Systems
```bash
pip3 install PyQt6 PyQt6-WebEngine PyQt6-Svg
python3 kiosk_browser.py
```

## ✨ Features

- **Modern Web Browser**: Full Qt6 WebEngine with YouTube, social media support
- **Quick Access Shortcuts**: Home Assistant, YouTube Music, Radio Browser, Google, YouTube
- **Radio Station Icons**: Beautiful custom and official icons for popular radio stations
- **Touchscreen Optimized**: Large buttons, virtual keyboard, gesture support
- **Raspberry Pi Ready**: Auto-detects Pi hardware, optimized for 1024x600 displays
- **Kiosk Mode**: Fullscreen interface with quick shortcuts to common sites
- **System Integration**: Systemd service, desktop integration, auto-start
- **Automatic Updates**: Zero-maintenance updates with no user prompts required

## 🔄 Automatic Updates

The Office Kiosk Browser features **fully automatic updates** with no user interaction required:

- ✅ **Zero Maintenance**: Checks and applies updates automatically on startup
- ✅ **No Prompts**: Updates are applied without any user confirmation
- ✅ **Auto-Restart**: Application restarts automatically with new version
- ✅ **Backup & Recovery**: Automatic backups before each update

**Configuration**: Updates are controlled by `scripts/update_config.conf`
```bash
AUTO_UPDATE_CHECK=true   # Check for updates on startup
AUTO_UPDATE_APPLY=true   # Apply updates automatically (no prompts)
```

For complete details, see: **[🔄 Automatic Updates Guide](docs/AUTOMATIC_UPDATES.md)**

## � Radio Station Icons

The kiosk features **professional radio station icons** with both official and custom designs:

- **Automatic Favicon Fetching**: Downloads official station icons where available
- **Custom SVG Icons**: Beautiful gradients and radio wave graphics for all stations
- **Brand Recognition**: Proper station branding improves user experience
- **Fallback System**: Ensures all stations always have appropriate icons

**Supported Stations:**
- 🎵 Jakaranda FM (Custom purple/green gradient)
- 📻 94.7 Highveld Stereo (Custom red/orange gradient)
- 🎶 KFM 94.5 (Custom blue/green gradient)
- 🗣️ Talk Radio 702 (Custom dark blue/gray gradient)
- ☁️ Sky Radio Hits (Official favicon + purple/orange)
- 🎧 Qmusic Non-Stop (Official favicon + pink/orange)

**Icon Creation**: Use `python scripts/create_radio_icons.py` to regenerate icons

## �📁 Project Structure

```
office_kiosk/
├── kiosk_browser.py          # Main application
├── config.ini                # Configuration
├── requirements.txt          # Dependencies
├── install/                  # Installation scripts
├── tests/                    # Test utilities
├── scripts/                  # Helper scripts
├── systemd/                  # Service files
├── docs/                     # Complete documentation
├── icons/                    # SVG assets
└── legacy/                   # Qt5 backup files
```

## 📖 Documentation

For complete installation, configuration, and troubleshooting guides, see:

**[📚 Complete Documentation](docs/README.md)**

Includes:
- Detailed installation instructions
- Hardware compatibility guide
- Configuration options
- Troubleshooting steps
- Development guidelines

## 🆘 Quick Help

**Installation Issues:**
```bash
./install/troubleshoot_pyqt6.sh
```

**Test Installation:**
```bash
python3 tests/test_qt_version.py
python3 tests/test_svg_icons.py
```

**Common Problems:**
- **Qt6 not found**: Use `./install/quick_install_pyqt6.sh`
- **SVG icons missing**: Install `python3-pyqt6.qtsvg`
- **Virtual keyboard**: Install `wvkbd` package
- **Multiple browser windows**: See [Multiple Instances Troubleshooting](docs/TROUBLESHOOTING_MULTIPLE_INSTANCES.md)

**Multiple Instances Issue:**
If you see multiple browser windows opening:
```bash
./install/trace_autostart.sh        # Quick diagnosis
./install/manage_autostart.sh stop   # Stop all instances
./install/manage_autostart.sh disable # Remove all autostart
./install/manage_autostart.sh enable  # Set up clean autostart
```

## 🔧 Requirements

- **OS**: Raspberry Pi OS Bookworm+ (recommended) or any Linux with Qt6
- **Hardware**: Raspberry Pi 3B+ or newer, 1GB+ RAM
- **Display**: Any resolution, optimized for 1024x600 touchscreens
- **Python**: 3.9+ with PyQt6, PyQt6-WebEngine, PyQt6-Svg

## Browser security and single-instance startup

The Qt6 browser blocks mixed-content execution, local-document access to other
files or remote resources, automatic JavaScript popups, and direct JavaScript
clipboard access. JavaScript and persistent login storage remain enabled.
Plain HTTP navigation to local services such as Home Assistant is supported;
local-network WebRTC remains enabled for camera streams.

The supplied startup and graphics scripts keep Chromium sandboxing enabled.
Run the browser as a regular desktop user. On Linux, sandbox support depends on
the kernel and distribution configuration; see the
[Qt platform notes](https://doc.qt.io/qt-6/qtwebengine-platform-notes.html#sandboxing-support).
Existing custom Chromium environment flags are still respected by the Python
entry point; remove old sandbox or web-security overrides from custom launchers.

One Qt6 browser instance per user is enforced through
`~/.office_kiosk_data/instance.lock`, shared across working directories and
repository copies. A second launch exits successfully without opening a window.
Lock or profile-directory errors stop startup with a nonzero exit code. Qt
recovers locks left by crashed processes automatically; do not delete a live
instance's lock file. Automatic restarts release the lock before relaunching
with the same Python interpreter and application arguments.

## � Autostart Setup

To automatically start the kiosk browser on boot:

```bash
# Enable autostart (run once after installation)
./install/setup_autostart.sh

# Or use the management script
./install/manage_autostart.sh enable
```

**Check autostart status:**
```bash
./install/manage_autostart.sh status
```

**Disable autostart:**
```bash
./install/manage_autostart.sh disable
```

The autostart setup configures multiple methods:
- **Desktop autostart** - starts when user logs into desktop
- **Systemd user service** - more robust, survives logout
- **Bashrc fallback** - backup method for shell logins

## �📄 License

MIT License - see LICENSE file for details
