#!/usr/bin/env python3
"""
Script to create radio station icons.
This script will:
1. Try to fetch official favicons from radio station websites
2. Create custom SVG icons as fallbacks
3. Update the home page HTML to use these icons
"""

import os
import sys
import requests
from urllib.parse import urljoin, urlparse
import base64
from PIL import Image
import io
import re

# Add the parent directory to sys.path so we can import from the main directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Radio stations data
RADIO_STATIONS = [
    {
        'name': 'Jakaranda FM',
        'filename': 'radio-jakaranda.svg',
        'website': 'https://www.jacarandafm.com/',
        'description': 'South African community radio station',
        'color_scheme': ['#8E44AD', '#27AE60'],  # Purple to Green
        'already_exists': True
    },
    {
        'name': '94.7 Highveld Stereo',
        'filename': 'radio-947.svg',
        'website': 'https://www.947.co.za/',
        'description': "Johannesburg's hit music station",
        'color_scheme': ['#E74C3C', '#F39C12'],  # Red to Orange
        'already_exists': False
    },
    {
        'name': 'KFM 94.5',
        'filename': 'radio-kfm.svg',
        'website': 'https://www.kfm.co.za/',
        'description': "Cape Town's hit music station",
        'color_scheme': ['#3498DB', '#2ECC71'],  # Blue to Green
        'already_exists': False
    },
    {
        'name': 'Talk Radio 702',
        'filename': 'radio-702.svg',
        'website': 'https://www.702.co.za/',
        'description': 'Johannesburg talk radio',
        'color_scheme': ['#34495E', '#95A5A6'],  # Dark Blue to Gray
        'already_exists': False
    },
    {
        'name': 'Sky Radio Hits',
        'filename': 'radio-sky.svg',
        'website': 'https://www.skyradio.nl/',
        'description': 'International hit music',
        'color_scheme': ['#9B59B6', '#E67E22'],  # Purple to Orange
        'already_exists': False
    },
    {
        'name': 'Qmusic Non-Stop',
        'filename': 'radio-qmusic.svg',
        'website': 'https://qmusic.nl/',
        'description': 'Continuous hit music',
        'color_scheme': ['#E91E63', '#FF5722'],  # Pink to Deep Orange
        'already_exists': False
    }
]

def fetch_favicon(url):
    """Try to fetch a favicon from a website."""
    try:
        print(f"  Trying to fetch favicon from {url}")
        
        # Try common favicon locations
        favicon_urls = [
            urljoin(url, '/favicon.ico'),
            urljoin(url, '/favicon.png'),
            urljoin(url, '/favicon.svg'),
            urljoin(url, '/apple-touch-icon.png'),
            urljoin(url, '/assets/favicon.ico'),
            urljoin(url, '/images/favicon.ico'),
        ]
        
        # Also try to parse the HTML for favicon links
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                # Look for favicon links in HTML
                favicon_patterns = [
                    r'<link[^>]*rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\'][^>]*href=["\']([^"\']+)["\']',
                    r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\']'
                ]
                
                for pattern in favicon_patterns:
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    for match in matches:
                        favicon_url = urljoin(url, match)
                        if favicon_url not in favicon_urls:
                            favicon_urls.insert(0, favicon_url)
        except:
            pass
        
        # Try to download each favicon URL
        for favicon_url in favicon_urls:
            try:
                print(f"    Trying: {favicon_url}")
                response = requests.get(favicon_url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200 and len(response.content) > 100:
                    print(f"    Success! Downloaded {len(response.content)} bytes")
                    return response.content
                    
            except Exception as e:
                print(f"    Failed: {e}")
                continue
                
        return None
        
    except Exception as e:
        print(f"  Error fetching favicon: {e}")
        return None

def convert_to_svg_data_url(image_data):
    """Convert image data to SVG-embedded data URL."""
    try:
        # Try to determine image format and convert to PNG if needed
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (remove alpha for better compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Resize to 64x64
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        
        # Convert to PNG
        png_buffer = io.BytesIO()
        img.save(png_buffer, format='PNG', optimize=True)
        png_data = png_buffer.getvalue()
        
        # Create base64 data URL
        b64_data = base64.b64encode(png_data).decode('ascii')
        data_url = f"data:image/png;base64,{b64_data}"
        
        return data_url
        
    except Exception as e:
        print(f"    Error converting image: {e}")
        return None

def create_custom_svg(station):
    """Create a custom SVG icon for a radio station."""
    name = station['name']
    colors = station['color_scheme']
    
    # Extract initials or abbreviation
    if 'FM' in name:
        parts = name.replace('FM', '').strip().split()
        if len(parts) > 1:
            abbrev = ''.join([p[0] for p in parts]) + 'FM'
        else:
            abbrev = parts[0][:3] + 'FM'
    elif any(char.isdigit() for char in name):
        # For stations with numbers (like 94.7, 702)
        numbers = ''.join([c for c in name if c.isdigit() or c == '.'])
        abbrev = numbers
    else:
        # For other stations, use first few letters
        clean_name = re.sub(r'[^A-Za-z]', '', name)
        abbrev = clean_name[:4].upper()
    
    # Limit abbreviation length
    if len(abbrev) > 6:
        abbrev = abbrev[:6]
    
    # Create SVG
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <!-- {name} -->
  <defs>
    <linearGradient id="{station['filename'].replace('.svg', '').replace('-', '')}Grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{colors[0]};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{colors[1]};stop-opacity:1" />
    </linearGradient>
  </defs>
  <circle cx="32" cy="32" r="30" fill="url(#{station['filename'].replace('.svg', '').replace('-', '')}Grad)" stroke="#fff" stroke-width="2"/>
  <text x="32" y="38" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="white" text-anchor="middle">{abbrev}</text>
  <!-- Radio waves -->
  <path d="M 45 20 Q 52 32 45 44" stroke="white" stroke-width="2" fill="none" opacity="0.7"/>
  <path d="M 48 24 Q 54 32 48 40" stroke="white" stroke-width="1.5" fill="none" opacity="0.5"/>
</svg>'''
    
    return svg_content

def process_radio_stations():
    """Process all radio stations to create icons."""
    icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    successful_icons = {}
    
    for station in RADIO_STATIONS:
        print(f"\nProcessing {station['name']}...")
        
        icon_path = os.path.join(icons_dir, station['filename'])
        
        # Skip if already exists (like Jakaranda)
        if station.get('already_exists') and os.path.exists(icon_path):
            print(f"  Icon already exists: {station['filename']}")
            successful_icons[station['name']] = station['filename']
            continue
        
        # Try to fetch favicon first
        favicon_data = fetch_favicon(station['website'])
        
        if favicon_data:
            # Try to create SVG with embedded favicon
            data_url = convert_to_svg_data_url(favicon_data)
            if data_url:
                svg_with_favicon = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <!-- {station['name']} - Official favicon -->
  <circle cx="32" cy="32" r="30" fill="url(#{station['filename'].replace('.svg', '').replace('-', '')}Grad)" stroke="#fff" stroke-width="2"/>
  <defs>
    <linearGradient id="{station['filename'].replace('.svg', '').replace('-', '')}Grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{station['color_scheme'][0]};stop-opacity:0.8" />
      <stop offset="100%" style="stop-color:{station['color_scheme'][1]};stop-opacity:0.8" />
    </linearGradient>
  </defs>
  <image href="{data_url}" x="12" y="12" width="40" height="40" />
  <!-- Radio waves -->
  <path d="M 45 20 Q 52 32 45 44" stroke="white" stroke-width="1.5" fill="none" opacity="0.6"/>
</svg>'''
                
                try:
                    with open(icon_path, 'w', encoding='utf-8') as f:
                        f.write(svg_with_favicon)
                    print(f"  Created icon with official favicon: {station['filename']}")
                    successful_icons[station['name']] = station['filename']
                    continue
                except Exception as e:
                    print(f"  Error saving SVG with favicon: {e}")
        
        # Fallback: create custom SVG
        print(f"  Creating custom SVG icon...")
        custom_svg = create_custom_svg(station)
        
        try:
            with open(icon_path, 'w', encoding='utf-8') as f:
                f.write(custom_svg)
            print(f"  Created custom icon: {station['filename']}")
            successful_icons[station['name']] = station['filename']
        except Exception as e:
            print(f"  Error saving custom SVG: {e}")
    
    return successful_icons

def update_home_page_html(successful_icons):
    """Update the home page HTML to use the new icons."""
    print(f"\nUpdating home page HTML...")
    
    main_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kiosk_browser.py')
    
    # Read the current file
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the icon mappings
    icon_mappings = {
        'Jakaranda FM': 'radio-jakaranda.svg',
        '94.7 Highveld Stereo': 'radio-947.svg',
        'KFM 94.5': 'radio-kfm.svg',
        'Talk Radio 702': 'radio-702.svg',
        'Sky Radio Hits': 'radio-sky.svg',
        'Qmusic Non-Stop': 'radio-qmusic.svg'
    }
    
    # Update each radio station link
    for station_name, icon_file in icon_mappings.items():
        if station_name in successful_icons:
            # Find the pattern for this station and replace the icon
            pattern = rf'(<div class="radio-name">)<span class="icon"[^>]*>[^<]*</span>(\s*{re.escape(station_name)})'
            replacement = rf'\1<img src="icons/{icon_file}" alt="{station_name}" class="radio-icon">\2'
            
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            print(f"  Updated icon for {station_name}")
    
    # Write the updated content back
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  Home page HTML updated successfully!")

def update_css_for_radio_icons():
    """Add CSS styles for radio icons."""
    print(f"\nAdding CSS styles for radio icons...")
    
    main_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kiosk_browser.py')
    
    # Read the current file
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add CSS for radio icons
    css_addition = '''
                .radio-icon {
                    width: 24px;
                    height: 24px;
                    margin-right: 8px;
                    vertical-align: middle;
                    border-radius: 50%;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }'''
    
    # Find the CSS section and add the new styles
    pattern = r'(\s+\.radio-name \{[^}]+\})'
    replacement = rf'\1{css_addition}'
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content, count=1)
        print("  Added CSS for radio icons")
    else:
        print("  Could not find CSS section to update")
    
    # Write the updated content back
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    print("Creating radio station icons...")
    print("=" * 50)
    
    # Install required packages if not available
    try:
        import requests
        from PIL import Image
    except ImportError:
        print("Installing required packages...")
        os.system("pip install requests Pillow")
        import requests
        from PIL import Image
    
    # Process all radio stations
    successful_icons = process_radio_stations()
    
    print(f"\n" + "=" * 50)
    print(f"Summary: Created {len(successful_icons)} radio station icons:")
    for name, filename in successful_icons.items():
        print(f"  - {name}: {filename}")
    
    # Update the home page HTML
    update_home_page_html(successful_icons)
    
    # Update CSS
    update_css_for_radio_icons()
    
    print(f"\nDone! All radio station icons have been created and the home page has been updated.")
