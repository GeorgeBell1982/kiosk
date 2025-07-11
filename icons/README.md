# SVG Icons Directory

This directory contains custom SVG icons used by the Office Kiosk Browser application.

## Icons Overview:

### Navigation Icons:
- **back.svg** - Left arrow for browser back navigation
- **forward.svg** - Right arrow for browser forward navigation  
- **refresh.svg** - Circular arrow for page refresh
- **home.svg** - House icon for home page
- **fullscreen.svg** - Expand icon for fullscreen toggle
- **shutdown.svg** - Power icon for Raspberry Pi shutdown

### Shortcut Icons:
- **homeassistant.svg** - Smart home icon for Home Assistant
- **music.svg** - Musical note icon for YouTube Music
- **google.svg** - Search icon for Google
- **youtube.svg** - Video play icon for YouTube
- **radio.svg** - General radio icon for radio browser
- **keyboard.svg** - Keyboard icon for virtual keyboard toggle (Pi only)

### Radio Station Icons:
- **radio-jakaranda.svg** - Jakaranda FM (Custom purple/green gradient)
- **radio-947.svg** - 94.7 Highveld Stereo (Custom red/orange gradient)  
- **radio-kfm.svg** - KFM 94.5 (Custom blue/green gradient)
- **radio-702.svg** - Talk Radio 702 (Custom dark blue/gray gradient)
- **radio-sky.svg** - Sky Radio Hits (Official favicon embedded)
- **radio-qmusic.svg** - Qmusic Non-Stop (Official favicon embedded)

## Automatic Icon Generation:

Use `../scripts/create_radio_icons.py` to automatically:
1. **Fetch official favicons** from radio station websites
2. **Create custom SVG icons** with gradients and radio wave graphics
3. **Update the home page HTML** to use the new icons
4. **Add proper CSS styling** for radio icons

The script intelligently falls back to custom designs when official icons aren't available.

## Design Notes:
- All icons are 64x64px SVG format for radio stations, 24x24px for others
- Designed to be visible on dark backgrounds with proper contrast
- Touch-friendly and scalable for various display sizes
- Radio icons feature gradients, station branding, and radio wave graphics
- Official favicons are embedded as base64 data when available
- Custom icons use color-coded gradients for easy station identification

## Usage:
Icons are loaded automatically by the `load_icon()` method in the main application.
Radio station icons are displayed via HTML `<img>` tags with CSS styling.
The icons scale proportionally based on button size for optimal visibility on 1024x600 displays.
