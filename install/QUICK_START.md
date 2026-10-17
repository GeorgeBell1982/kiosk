# PyQt6 Build Scripts - Quick Reference

## 🚀 One-Command Installation

Just run this on your Raspberry Pi:

```bash
# Make executable (if needed)
chmod +x install/*.sh

# Try automatic installation (recommended)
bash install/quick_install_pyqt6.sh
```

This will:
1. ✅ Try system packages (fastest - 5 minutes)
2. ✅ Try piwheels (fast - 10 minutes) 
3. ✅ Try regular pip (medium - 30 minutes)
4. Source builds are attempted only with `--build-from-source` (can take hours).

## 📁 Available Scripts

| Script | Purpose | Time | When to Use |
|--------|---------|------|-------------|
| `quick_install_pyqt6.sh` | **Automatic installation** | 5min-8hrs | **Start here - tries all methods** |
| `build_pyqt6_rpi.sh` | Full source build | 4-8 hours | When system packages unavailable |
| `troubleshoot_pyqt6.sh` | Diagnose issues | 5 minutes | When things don't work |

## 🔧 Manual Build Process

If you specifically want to build from source:

```bash
# Full manual build (takes several hours)
bash install/build_pyqt6_rpi.sh
```

This will:
- ✅ Check system requirements
- ✅ Install dependencies
- ✅ Build Qt6 (if needed)
- ✅ Build PyQt6
- ✅ Build WebEngine (if possible)
- ✅ Test installation

## 🐛 Troubleshooting

If you have issues:

```bash
# Comprehensive diagnostics
bash install/troubleshoot_pyqt6.sh

# Generate detailed report
bash install/troubleshoot_pyqt6.sh report
```

## ✅ Success Check

After installation, verify it works:

```bash
# Test Qt versions
python3 test_qt_version.py

# Run kiosk browser
python3 kiosk_browser.py
```

## 📋 What Gets Built

The scripts will install/build:
- **Qt6 Core** (widgets, GUI framework)
- **Qt6 WebEngine** (modern browser engine for YouTube compatibility)
- **PyQt6** (Python bindings)
- **PyQt6-WebEngine** (Python web engine bindings)

## 🏗️ Pi Model Support

| Model | Qt6 Support | Build Time | Performance |
|-------|-------------|------------|-------------|
| **Pi 5** | ✅ Excellent | 2-4 hours | Best |
| **Pi 4** | ✅ Good | 4-6 hours | Good |
| **Pi 3** | ⚠️ Limited | 6-8 hours | Basic |
| **Pi 2** | ❌ Not recommended | 8+ hours | Poor |

## 🎯 Expected Results

After successful installation:
- ✅ YouTube works without "outdated browser" errors
- ✅ Modern websites load properly  
- ✅ Better video performance
- ✅ Enhanced security with latest Qt6

## 🔄 Fallback Plan

If Qt6 doesn't work well:

```bash
# Use Qt5 backup version
python3 kiosk_browser_qt5_backup.py

# Or permanently switch back
cp kiosk_browser_qt5_backup.py kiosk_browser.py
```

---

**Ready to try PyQt6 on your Pi? Start with:**
```bash
bash install/quick_install_pyqt6.sh
```
