# Qt6 Migration Guide

## Overview
The Office Kiosk Browser has been upgraded from Qt5 to Qt6 for better modern web compatibility, especially with YouTube and other streaming services.

## What's Changed

### Benefits of Qt6
- ✅ **No More "Outdated Browser" Errors**: Modern Chromium engine that YouTube recognizes
- ✅ **Better Video Support**: Improved codec support and hardware acceleration
- ✅ **Enhanced Security**: Latest security updates and patches
- ✅ **Future-Proof**: Qt6 is actively developed, Qt5 is in maintenance mode

### File Changes
- `kiosk_browser.py` → Now uses Qt6 (was Qt5)
- `kiosk_browser_qt5_backup.py` → Backup of original Qt5 version
- `requirements.txt` → Updated to use PyQt6 packages
- `install_rpi.sh` → Updated to prefer Qt6 installation

## Migration Steps

### For Raspberry Pi Users

#### Option 1: Fresh Installation (Recommended)
```bash
# Update your system first
sudo apt update && sudo apt upgrade -y

# Install Qt6 packages (Raspberry Pi OS Bookworm and later)
sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine

# Test the installation
python3 test_qt_version.py

# If Qt6 is available, you're ready!
python3 kiosk_browser.py
```

#### Option 2: Fallback to Qt5
If Qt6 is not available on your system:
```bash
# Use the Qt5 backup version
cp kiosk_browser_qt5_backup.py kiosk_browser.py

# Or run it directly
python3 kiosk_browser_qt5_backup.py
```

### For Windows/Development Users
```bash
# Activate your virtual environment
# Install Qt6 packages
pip install PyQt6 PyQt6-WebEngine

# Test
python test_qt_version.py

# Run the application
python kiosk_browser.py
```

## Troubleshooting

### "No module named PyQt6"
**Solution**: Install Qt6 packages
```bash
# Raspberry Pi
sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine

# Other systems
pip install PyQt6 PyQt6-WebEngine
```

### Qt6 Not Available on Older Systems
**Solution**: Use the Qt5 backup
```bash
python3 kiosk_browser_qt5_backup.py
```

### Performance Issues
- Qt6 may use more resources than Qt5
- If performance is poor, consider using the Qt5 backup
- Ensure your Raspberry Pi has adequate RAM (4GB+ recommended for Qt6)

## Verification

Use the provided test script to check your setup:
```bash
python3 test_qt_version.py
```

This will tell you:
- Which Qt versions are available
- Which one to use
- How to run the application

## Rollback Plan

If you experience issues with Qt6, you can easily rollback:
```bash
# Replace main file with Qt5 backup
cp kiosk_browser_qt5_backup.py kiosk_browser.py

# Update requirements to Qt5
cp requirements-qt5.txt requirements.txt  # If this file exists

# Reinstall Qt5 packages
sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine
```

## Support

- Run `python3 test_qt_version.py` for compatibility check
- Check logs for error details
- Use Qt5 backup version if Qt6 causes issues
- Consider upgrading to newer Raspberry Pi OS for better Qt6 support
