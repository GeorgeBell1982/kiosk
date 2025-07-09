# Test Scripts

Verification and testing utilities for the Office Kiosk Browser.

## Available Tests

### `test_qt_version.py`
Tests Qt6 installation and reports version information.
```bash
python3 test_qt_version.py
```

**Checks:**
- PyQt6 availability
- Qt6 WebEngine support
- Version compatibility
- Import functionality

### `test_svg_icons.py` 
Visual test for SVG icon support and rendering.
```bash
python3 test_svg_icons.py
```

**Features:**
- Tests all available icons
- Shows SVG rendering capability
- Demonstrates fallback behavior
- GUI test window with all icons

### `test_virtual_keyboard.sh`
Tests virtual keyboard (wvkbd) functionality on Raspberry Pi.
```bash
./test_virtual_keyboard.sh
```

**Features:**
- Environment detection (Wayland vs X11)
- wvkbd installation check and auto-install
- Process management testing
- Compact keyboard testing (180px/160px height)
- Bottom-anchored positioning test
- Overlay layer compatibility test
- Manual test command suggestions
- Troubleshooting guidance

**Raspberry Pi Only** - This test is designed for Pi hardware with touchscreen support.

### `test_home_assistant_storage.py`
Interactive GUI test for Home Assistant login persistence.
```bash
python3 tests/test_home_assistant_storage.py
```

**Features:**
- Tests Qt6 WebEngine storage configuration
- Checks persistent storage paths and permissions
- Provides buttons to test cookie persistence
- Allows clearing storage for fresh testing
- Shows real-time storage status
- Load test Home Assistant instance
- Verify login persistence across sessions

### `test_home_assistant_storage.sh`
Command-line script to diagnose Home Assistant storage issues.
```bash
bash tests/test_home_assistant_storage.sh
```

**Checks:**
- Storage directory permissions and contents
- Cookie and session files detection
- Qt6 WebEngine configuration in main app
- Provides troubleshooting recommendations
- Storage usage statistics
- File system write permissions

## Usage

Run tests after installation to verify everything works:

```bash
# Basic Qt6 test
python3 tests/test_qt_version.py

# Visual icon test  
python3 tests/test_svg_icons.py

# Full application test
python3 kiosk_browser.py
```

## Expected Results

**Successful Qt6 Test:**
```
✅ Qt6 QtWidgets available
✅ Qt6 QtWebEngine available  
✅ Qt6 QtSvg available
Qt Version: 6.x.x
PyQt Version: 6.x.x
```

**Successful Icon Test:**
- GUI window opens showing all icons
- Icons display as graphics (not text)
- No error messages in console

**Successful Home Assistant Storage Test:**
- Storage directory exists and is writable
- Configuration shows ForcePersistentCookies enabled
- Cookie files are created when logging in
- Login persists across browser restarts

## Troubleshooting

If tests fail, run the troubleshoot script:
```bash
./install/troubleshoot_pyqt6.sh
```
