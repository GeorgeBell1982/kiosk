# PyQt6 Build Scripts for Raspberry Pi

This directory contains automated scripts to help you install and build PyQt6 on your Raspberry Pi.

## 🚀 Quick Start

### Option 1: Quick Install (Recommended)
Try multiple installation methods automatically:
```bash
chmod +x install/quick_install_pyqt6.sh
bash install/quick_install_pyqt6.sh
```

### Option 2: Full Build from Source
If system packages don't work, build everything from source:
```bash
chmod +x install/build_pyqt6_rpi.sh
bash install/build_pyqt6_rpi.sh
```

### Option 3: Troubleshooting
Diagnose and fix PyQt6 issues:
```bash
chmod +x install/troubleshoot_pyqt6.sh
bash install/troubleshoot_pyqt6.sh
```

## 📁 Scripts Overview

### `quick_install_pyqt6.sh`
**Recommended for most users**
- Tries system packages first (fastest)
- Falls back to piwheels (pre-compiled ARM packages)
- Falls back to regular pip
- Source builds require `--build-from-source`
- **Time**: 5-30 minutes depending on method

### `build_pyqt6_rpi.sh`
**For when you need full control or system packages aren't available**
- Builds Qt6 and PyQt6 from source
- Optimized for different Pi models
- Handles memory management and swap
- Includes comprehensive error handling
- **Time**: 4-8 hours depending on Pi model

### `troubleshoot_pyqt6.sh`
**For diagnosing problems**
- Comprehensive system diagnostics
- Checks Qt and Python installations
- Identifies common issues
- Attempts automatic fixes
- Generates detailed reports

## 🔧 Installation Methods (in order of preference)

### 1. System Packages (Fastest - 5 minutes)
```bash
sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine
```
- **Pros**: Fast, reliable, maintained by OS
- **Cons**: May not be available on older Pi OS versions

### 2. Piwheels (Fast - 10 minutes)
```bash
pip install --extra-index-url https://www.piwheels.org/simple/ PyQt6 PyQt6-WebEngine
```
- **Pros**: Pre-compiled for ARM, usually works
- **Cons**: May lag behind latest versions

### 3. Regular Pip (Medium - 30 minutes)
```bash
pip install PyQt6 PyQt6-WebEngine
```
- **Pros**: Latest versions, widely compatible
- **Cons**: May need compilation, slower

### 4. Build from Source (Slow - 4-8 hours)
```bash
bash install/build_pyqt6_rpi.sh
```
- **Pros**: Full control, custom optimizations
- **Cons**: Very time consuming, complex

## 🏗️ Build Requirements

### Minimum System Requirements
- **Raspberry Pi 3 or newer** (Pi 4 recommended for Qt6)
- **2GB+ RAM** (4GB recommended for Qt6)
- **8GB+ free disk space** for build process
- **Raspberry Pi OS Bullseye or newer**
- **Active internet connection**

### Recommended Setup
- **Pi 4 with 4GB+ RAM**
- **32GB+ SD card** (Class 10 or better)
- **Active cooling** (builds generate heat)
- **Stable power supply**

## 🎯 Pi Model Optimizations

The build scripts automatically optimize based on your Pi model:

### Pi 5 (Best)
- Full parallel build (`-j4` or more)
- All Qt6 features enabled
- Hardware acceleration support
- **Build time**: ~2-4 hours

### Pi 4 (Good)
- Parallel build (`-j4`)
- Most Qt6 features enabled
- Good performance
- **Build time**: ~4-6 hours

### Pi 3 (Limited)
- Reduced parallelism (`-j2`)
- Some features disabled for stability
- May need extra swap space
- **Build time**: ~6-8 hours

### Pi 2 and older (Not Recommended)
- Single-threaded build (`-j1`)
- Minimal feature set
- Very slow, may fail
- **Build time**: ~8+ hours

## 🐛 Common Issues and Solutions

### "No module named PyQt6"
```bash
# Try different installation methods
bash install/quick_install_pyqt6.sh
```

### "Qt6 not found" or qmake6 missing
```bash
# Install Qt6 development packages
sudo apt install qt6-base-dev qt6-tools-dev
```

### Build runs out of memory
```bash
# The script automatically adds swap, but you can add more:
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### YouTube still shows "outdated browser"
```bash
# Test if Qt6 WebEngine is working:
bash install/troubleshoot_pyqt6.sh test
# If WebEngine failed, try rebuilding with:
bash install/build_pyqt6_rpi.sh
```

### Build fails with compilation errors
```bash
# Check system requirements and try troubleshooter:
bash install/troubleshoot_pyqt6.sh
# Update system packages:
sudo apt update && sudo apt upgrade
```

## 📊 Performance Expectations

### Pi 5 (Excellent)
- ✅ Full Qt6 support
- ✅ WebEngine works well
- ✅ Smooth YouTube playback
- ✅ Good for 1080p content

### Pi 4 (Good)
- ✅ Qt6 support
- ✅ WebEngine mostly works
- ⚠️ 720p YouTube recommended
- ⚠️ May need cooling for long sessions

### Pi 3 (Limited)
- ⚠️ Basic Qt6 support
- ❌ WebEngine may be unreliable
- ❌ Consider using Qt5 version instead
- ❌ 480p video recommended

## 🔄 Fallback Options

If Qt6 doesn't work well on your Pi:

### Use Qt5 Backup
```bash
# Use the Qt5 version instead
python3 kiosk_browser_qt5_backup.py
```

### Permanently Switch to Qt5
```bash
# Replace main file with Qt5 version
cp kiosk_browser_qt5_backup.py kiosk_browser.py
# Install Qt5 packages
sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine
```

## 📋 Testing Your Installation

After installation, test with:
```bash
# Check Qt compatibility
python3 test_qt_version.py

# Test kiosk browser
python3 kiosk_browser.py

# Full diagnostic
bash install/troubleshoot_pyqt6.sh test
```

## 🆘 Getting Help

1. **Run diagnostics first**:
   ```bash
   bash install/troubleshoot_pyqt6.sh report
   ```

2. **Check the generated report** in `/tmp/pyqt6_diagnostic_*.txt`

3. **Try different installation methods**:
   ```bash
   bash install/quick_install_pyqt6.sh
   ```

4. **For build issues**, check:
   - Available disk space (`df -h`)
   - Available memory (`free -h`)
   - System temperature (`vcgencmd measure_temp`)
   - Build logs in the build directory

## 🏁 Success Indicators

Your PyQt6 installation is working when:
- ✅ `python3 test_qt_version.py` shows Qt6 recommended
- ✅ `python3 kiosk_browser.py` starts without errors
- ✅ YouTube loads without "outdated browser" warnings
- ✅ Home Assistant and other sites work properly

Happy building! 🎉
