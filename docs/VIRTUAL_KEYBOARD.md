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

### Keyboard doesn't appear
1. Check if wvkbd is installed: `which wvkbd-mobintl`
2. Test manually: `wvkbd-mobintl --landscape --height 250`
3. Check display manager (works best with Wayland)

### Button not visible
- Virtual keyboard button only appears on Raspberry Pi
- For testing on other systems, the button is hidden

### Keyboard appears in wrong position
- wvkbd automatically positions itself at the bottom
- Adjust height with `--height` parameter if needed

## Alternative Keyboards

If wvkbd is not suitable, you can modify the `toggle_virtual_keyboard()` method to use:
- `onboard`: GNOME's virtual keyboard
- `florence`: Cross-platform virtual keyboard
- `squeekboard`: Phosh's virtual keyboard

## Configuration

The keyboard is configured with optimal settings for the kiosk browser:
- Height: 250 pixels
- Layout: Mobile international (mobintl)
- Position: Bottom of screen
- Margins: 5 pixels

These settings can be adjusted in the `toggle_virtual_keyboard()` method in `kiosk_browser.py`.
