# Installation Scripts

This directory contains automated installation and troubleshooting scripts for the Office Kiosk Browser.

## Quick Install (Recommended)

**For most users:**
```bash
./quick_install_pyqt6.sh
```

Automatically detects your system, installs all dependencies, and verifies the installation.

## Advanced Installation

**For custom builds or older systems:**
```bash
./build_pyqt6_rpi.sh
```

Builds PyQt6 from source (takes several hours).

## Troubleshooting

**If you encounter problems:**
```bash
./troubleshoot_pyqt6.sh
```

Runs comprehensive diagnostics and attempts automatic fixes.

## Files

- `quick_install_pyqt6.sh` - Main installation script with multiple fallback methods
- `build_pyqt6_rpi.sh` - Source build script for custom installations  
- `troubleshoot_pyqt6.sh` - Diagnostic and repair tool
- `README.md` - Detailed installation documentation
- `QUICK_START.md` - Quick reference guide
