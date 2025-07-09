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
- **Touchscreen Optimized**: Large buttons, virtual keyboard, gesture support
- **Raspberry Pi Ready**: Auto-detects Pi hardware, optimized for 1024x600 displays
- **Kiosk Mode**: Fullscreen interface with quick shortcuts to common sites
- **System Integration**: Systemd service, desktop integration, auto-start

## 📁 Project Structure

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

## 🔧 Requirements

- **OS**: Raspberry Pi OS Bookworm+ (recommended) or any Linux with Qt6
- **Hardware**: Raspberry Pi 3B+ or newer, 1GB+ RAM
- **Display**: Any resolution, optimized for 1024x600 touchscreens
- **Python**: 3.9+ with PyQt6, PyQt6-WebEngine, PyQt6-Svg

## 📄 License

MIT License - see LICENSE file for details
