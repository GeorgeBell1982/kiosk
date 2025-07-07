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

## Design Notes:
- All icons are 24x24px SVG format
- Designed to be visible on dark backgrounds
- Touch-friendly and scalable
- White fill color for maximum contrast
- Some icons include colored accents for visual appeal

## Usage:
Icons are loaded automatically by the `load_icon()` method in the main application.
The icons scale proportionally based on button size for optimal visibility on 1024x600 displays.
