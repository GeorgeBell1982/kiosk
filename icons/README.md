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

## Home-page station logos

The home page embeds these bundled logos as data URLs, so rendering does not
contact station websites. Names remain visible alongside every logo.

Downloaded from the stations' official sites on 2026-10-17:

- `radio-jacaranda.png`: https://turntable.kagiso.io/images/Jac_Logo.max-140x140.png (Jacaranda website logo)
- `radio-947.png`: https://www.primediaplus.com/images/logos/logo-947.png
- `radio-kfm.png`: https://www.primediaplus.com/images/logos/logo-kfm.png
- `radio-702.png`: https://www.primediaplus.com/images/logos/logo-702.png
- `radio-hot.png`: https://hot1027.co.za/wp-content/uploads/2025/03/favicon-300x300.png

Sky Radio and Qmusic reuse the embedded favicons in `radio-sky.svg` and
`radio-qmusic.svg`. The older custom South African SVGs remain for legacy uses.
Station names and logos belong to their respective owners.

Added on 2026-10-23: `radio-groot.jpg` from Groot FM's official iono.fm player:
https://cdn.iono.fm/files/p274/logo_274_20250908_202204_350.jpeg
The broadcaster links to https://iframe.iono.fm/s/330; its playlist at
https://iframe.iono.fm/playlists/stream/330 lists the direct MP3 stream.
