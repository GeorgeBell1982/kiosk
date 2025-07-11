#!/usr/bin/env python3
"""
Script to embed all home page icons as data URLs.
This script will replace all Unicode icons in the home page HTML with embedded SVG data URLs.
"""

import os
import base64
import re

def read_svg_file(icon_name):
    """Read an SVG file and return its content."""
    icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icons')
    icon_path = os.path.join(icons_dir, f'{icon_name}.svg')
    
    if os.path.exists(icon_path):
        with open(icon_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def create_simple_svg_icon(icon_type, size=24):
    """Create a simple SVG icon when no file exists."""
    icons = {
        'computer': '''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="4" width="18" height="12" rx="1" fill="#a8e6cf" stroke="#fff" stroke-width="1"/>
  <rect x="8" y="18" width="8" height="2" fill="#a8e6cf"/>
  <rect x="6" y="20" width="12" height="1" fill="#a8e6cf"/>
</svg>''',
        'sparkle': '''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 2L14 8L20 10L14 12L12 18L10 12L4 10L10 8Z" fill="#ffd700" stroke="#fff" stroke-width="0.5"/>
  <circle cx="18" cy="6" r="1" fill="#ffd700"/>
  <circle cx="6" cy="18" r="1" fill="#ffd700"/>
</svg>''',
        'radio': '''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="9" width="18" height="10" rx="2" fill="#9b59b6" stroke="#fff" stroke-width="1"/>
  <circle cx="7" cy="14" r="1.5" fill="#fff"/>
  <rect x="11" y="12" width="8" height="1" fill="#fff"/>
  <rect x="11" y="14" width="6" height="1" fill="#fff"/>
  <rect x="11" y="16" width="4" height="1" fill="#fff"/>
  <path d="M9 5 L15 7" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
</svg>''',
        'home': '''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 3L2 12H5V20H19V12H22L12 3Z" fill="#e74c3c" stroke="#fff" stroke-width="1"/>
  <rect x="9" y="14" width="2" height="4" fill="#fff"/>
  <rect x="13" y="14" width="2" height="2" fill="#fff"/>
</svg>''',
        'music': '''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M8 18C8 19.1 7.1 20 6 20S4 19.1 4 18 4.9 16 6 16 8 16.9 8 18Z" fill="#e67e22"/>
  <path d="M20 16C20 17.1 19.1 18 18 18S16 17.1 16 16 16.9 14 18 14 20 14.9 20 16Z" fill="#e67e22"/>
  <path d="M8 18V6L20 4V16" stroke="#e67e22" stroke-width="2" fill="none" stroke-linecap="round"/>
</svg>''',
        'search': '''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="10" cy="10" r="6" fill="none" stroke="#27ae60" stroke-width="2"/>
  <path d="M20 20L16 16" stroke="#27ae60" stroke-width="2" stroke-linecap="round"/>
</svg>''',
        'video': '''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="6" width="20" height="12" rx="2" fill="#c0392b" stroke="#fff" stroke-width="1"/>
  <path d="M10 9L15 12L10 15V9Z" fill="#fff"/>
</svg>'''
    }
    
    return icons.get(icon_type, '').format(size=size)

def svg_to_data_url(svg_content):
    """Convert SVG content to a data URL."""
    if not svg_content:
        return None
    
    # Clean up the SVG content
    svg_content = svg_content.strip()
    
    # Encode as base64
    b64_data = base64.b64encode(svg_content.encode('utf-8')).decode('ascii')
    return f"data:image/svg+xml;base64,{b64_data}"

def update_home_page_icons():
    """Update the home page HTML to use embedded SVG icons."""
    print("Updating home page icons...")
    
    main_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kiosk_browser.py')
    
    # Read the current file
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Icon mappings: Unicode -> (icon_file_name, fallback_type)
    icon_mappings = [
        (r'&#x1F4BB;', 'computer', 'Computer icon'),  # Computer
        (r'&#x2728;', 'sparkle', 'Sparkle icon'),      # Sparkle  
        (r'&#x1F4FB;', 'radio', 'Radio icon'),         # Radio
        (r'&#x1F3E0;', 'home', 'Home icon'),           # Home
        (r'&#x1F3B5;', 'music', 'Music icon'),         # Music note
        (r'&#x1F50D;', 'search', 'Search icon'),       # Magnifying glass
        (r'&#x1F4FA;', 'video', 'Video icon'),         # Television
    ]
    
    # Replace each Unicode icon with an embedded SVG
    for unicode_char, icon_type, alt_text in icon_mappings:
        print(f"  Processing {alt_text}...")
        
        # Try to read existing SVG file first
        svg_content = None
        possible_names = [icon_type, f'home_{icon_type}', f'icon_{icon_type}']
        
        for name in possible_names:
            svg_content = read_svg_file(name)
            if svg_content:
                print(f"    Found existing SVG: {name}.svg")
                break
        
        # If no existing SVG, create a simple one
        if not svg_content:
            svg_content = create_simple_svg_icon(icon_type, 20)  # Smaller for inline use
            print(f"    Created simple SVG for {icon_type}")
        
        if svg_content:
            data_url = svg_to_data_url(svg_content)
            if data_url:
                # Replace the Unicode character with an img tag
                pattern = rf'<span class="icon"[^>]*>{unicode_char}</span>'
                replacement = f'<img src="{data_url}" alt="{alt_text}" class="home-icon">'
                
                # Count replacements
                old_content = content
                content = re.sub(pattern, replacement, content)
                replacements = len(re.findall(pattern, old_content))
                if replacements > 0:
                    print(f"    Replaced {replacements} instances of {unicode_char}")
                else:
                    print(f"    No instances of {unicode_char} found")
    
    # Add CSS for home icons
    css_addition = '''
                .home-icon {
                    width: 20px;
                    height: 20px;
                    margin-right: 8px;
                    vertical-align: middle;
                    display: inline-block;
                }'''
    
    # Find the radio-icon CSS and add home-icon CSS after it
    pattern = r'(\s+\.radio-icon \{[^}]+\})'
    if re.search(pattern, content):
        content = re.sub(pattern, rf'\1{css_addition}', content, count=1)
        print("  Added CSS for home icons")
    else:
        print("  Could not find CSS section to update")
    
    # Write the updated content back
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  Home page HTML updated successfully!")

if __name__ == "__main__":
    print("Embedding home page icons as data URLs...")
    print("=" * 50)
    
    update_home_page_icons()
    
    print(f"\nDone! All home page icons have been embedded as data URLs.")
