# Test Scripts

Verification and testing utilities for the Office Kiosk Browser.

## Available Tests

### `test_radio_player.py`
Offline tests run the radio JavaScript in Qt WebEngine with deterministic audio
and timer substitutes. Covers station selection, play/stop, backoff, stalled
streams, stale events/promises, online recovery, volume, missing MP3 support,
policy errors, panel reuse, browser navigation and application shutdown. Requires
PyQt6 and PyQt6-WebEngine. Live station availability is not part of this suite.

```bash
python -m unittest discover -s tests -p test_radio_player.py -v
```


### `test_installation_scripts.py`
Tests launcher argument and exit-code handling, dependency failures, graphical
session checks, desktop-entry quoting, unattended installation, and safe autostart
management. OS-changing commands are stubbed, and fixtures use the OS temporary
directory. Windows additionally tests the actual batch and PowerShell launchers
with a temporary Python environment. Requires Python and Bash; no Qt installation,
package installation, service activation, or live desktop is needed.

```bash
python -m unittest discover -s tests -p test_installation_scripts.py -v
```

### `test_reliability.py`
Automated headless regression tests for persistent browser profiles, browser
security settings, blocked local-file reads, navigation to local HTTP services,
update restart timers, and update checks launched outside the project directory.
Separate-process tests cover competing launches, crash recovery, lock failures,
and release of the profile lock before restarting. Browser tests also cover
verbose updater output, failed process startup, and developer-tools lifetime.
Requires PyQt6 and PyQt6-WebEngine; the update-script test also requires Bash
(Git for Windows is supported). External update actions are stubbed.

```bash
python -m unittest discover -s tests -p test_reliability.py -v
```

### `test_update_script.py`
Tests updater policy, unprivileged logging, backup failures, and dependency
installation error reporting. Local Git repositories verify fast-forward
updates and skipping ahead or diverged branches. No network or production
checkout is used. Requires Git and Bash; Qt is not required.

```bash
python -m unittest discover -s tests -p test_update_script.py -v
```

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
- Installation check with instructions; never installs packages automatically
- Compact 180px keyboard in portrait and landscape orientations
- Five-second manual visibility and typing check
- Stops only its own child process, including when interrupted

**Raspberry Pi Only** - This test is designed for Pi hardware with touchscreen support.

### `test_touch_keyboard.py`
Headless Qt regression tests for keyboard startup and cancellation, owned-process
cleanup, failure reporting, bounded diagnostics, fullscreen restoration, and
responsive touch-target geometry. Includes a real WebEngine text-field focus
test and fullscreen shortcuts with page focus. Child processes substitute for
wvkbd, so this does not validate the Wayland compositor or physical touch input.

```bash
python -m unittest discover -s tests -p test_touch_keyboard.py -v
```

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
