# Virtual Keyboard Setup for Office Kiosk Browser

The Office Kiosk Browser includes support for toggling a virtual keyboard on Raspberry Pi using `wvkbd` (Wayland Virtual Keyboard).

## Installation

### Automatic Installation (Raspberry Pi OS Bookworm+)
```bash
sudo apt update
sudo apt install wvkbd
```

### Manual Installation (if not available in repositories)
```bash
# Install dependencies
sudo apt install build-essential meson ninja-build pkg-config
sudo apt install libwayland-dev libxkbcommon-dev libcairo2-dev libpango1.0-dev

# Clone and build wvkbd
git clone https://github.com/jjsullivan5196/wvkbd.git
cd wvkbd
meson build
ninja -C build
sudo ninja -C build install
```

## Usage

1. **Start the Office Kiosk Browser**: `python3 kiosk_browser.py`
2. **Toggle Keyboard**: Click the keyboard button (⌨) in the control panel
3. **Button States**:
   - **Gray**: Keyboard hidden
   - **Orange**: Keyboard visible

## Features

- **Automatic positioning**: Keyboard appears at the bottom of the screen
- **Landscape layout**: Optimized for touchscreen use
- **Clean shutdown**: Keyboard automatically hides when app closes
- **Visual feedback**: Button changes color to show keyboard state
- **Touch-friendly**: Large keys suitable for finger input

## Keyboard Layout

wvkbd provides a mobile-style keyboard with:
- QWERTY layout in landscape mode
- Number row
- Common symbols and punctuation
- Backspace, Enter, and Space keys
- Shift for uppercase letters

## Troubleshooting

### Keyboard Not Visible
If the virtual keyboard doesn't appear when clicked:

1. **Check if wvkbd is running**:
   ```bash
   pgrep wvkbd-mobintl
   ```

2. **Manually test keyboard**:
   ```bash
   wvkbd-mobintl -L -H 280
   ```

3. **Check window manager compatibility**:
   - The keyboard works best with Wayland compositors
   - On X11, you may need additional window manager tools like `wmctrl`
   - Install wmctrl for better window management: `sudo apt install wmctrl`

4. **If keyboard appears behind browser**:
   - The browser automatically tries to raise the keyboard window
   - Try clicking in a text field first, then toggle the keyboard
   - Switch to a different virtual terminal and back: `Ctrl+Alt+F2`, then `Ctrl+Alt+F7`

5. **Alternative keyboard activation**:
   ```bash
   # Kill any existing keyboard
   pkill wvkbd-mobintl
   
   # Start with basic settings
   wvkbd-mobintl -L -H 280
   ```

### Button Icons Too Large
If navigation button icons appear too large:
- The latest version reduces icon size from 40% to 25% of button size
- Icons should now better match the SVG designs
- Restart the application after updates

## Configuration

The keyboard is configured with optimal settings for the kiosk browser:
- Height: 280-300 pixels (Wayland uses 300px, X11 uses 280px)  
- Layout: Mobile international (mobintl)
- Landscape mode: `-L` flag for proper orientation
- Colors: Semi-transparent background on Wayland for better visibility
- Command flags: `-H` for height (not `--height`)

These settings can be adjusted in the `toggle_virtual_keyboard()` method in `kiosk_browser.py`.
