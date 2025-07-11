#!/usr/bin/env python3
"""
Script to embed SVG icons directly into the home page HTML.
This fixes the issue where relative paths don't work with setHtml().
"""

import os
import sys
import base64
import re

def svg_to_data_url(svg_file_path):
    """Convert SVG file to data URL for embedding in HTML."""
    try:
        with open(svg_file_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Optimize SVG content - remove unnecessary whitespace and newlines
        svg_content = re.sub(r'\s+', ' ', svg_content)
        svg_content = svg_content.strip()
        
        # Create data URL
        data_url = f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode('utf-8')).decode('ascii')}"
        return data_url
        
    except Exception as e:
        print(f"Error processing {svg_file_path}: {e}")
        return None

def update_radio_icons_in_html():
    """Update the main file to use embedded SVG data URLs."""
    
    # Define the radio station icons to embed
    radio_icons = {
        'Jakaranda FM': 'radio-jakaranda.svg',
        '94.7 Highveld Stereo': 'radio-947.svg', 
        'KFM 94.5': 'radio-kfm.svg',
        'Talk Radio 702': 'radio-702.svg',
        'Sky Radio Hits': 'radio-sky.svg',
        'Qmusic Non-Stop': 'radio-qmusic.svg'
    }
    
    # Get the icons directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    icons_dir = os.path.join(project_dir, 'icons')
    main_file = os.path.join(project_dir, 'kiosk_browser.py')
    
    print("Converting SVG icons to data URLs...")
    
    # Convert each SVG to data URL
    icon_data_urls = {}
    for station_name, icon_filename in radio_icons.items():
        icon_path = os.path.join(icons_dir, icon_filename)
        if os.path.exists(icon_path):
            data_url = svg_to_data_url(icon_path)
            if data_url:
                icon_data_urls[station_name] = data_url
                print(f"  ✓ {station_name}: {len(data_url)} chars")
            else:
                print(f"  ✗ {station_name}: Failed to convert")
        else:
            print(f"  ✗ {station_name}: File not found: {icon_path}")
    
    if not icon_data_urls:
        print("No icons were converted successfully!")
        return False
    
    # Read the main file
    print(f"\nUpdating {main_file}...")
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading main file: {e}")
        return False
    
    # Replace each radio station icon reference
    updates_made = 0
    for station_name, data_url in icon_data_urls.items():
        # Find and replace the img src for this station
        pattern = rf'(<img src="icons/radio-[^"]*" alt="{re.escape(station_name)}" class="radio-icon">)'
        replacement = f'<img src="{data_url}" alt="{station_name}" class="radio-icon">'
        
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            updates_made += 1
            print(f"  ✓ Updated {station_name}")
        else:
            print(f"  ✗ Could not find pattern for {station_name}")
    
    if updates_made == 0:
        print("No updates were made!")
        return False
    
    # Write the updated content back
    try:
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ Successfully updated {updates_made} radio station icons!")
        print("Icons are now embedded as data URLs and should display correctly.")
        return True
    except Exception as e:
        print(f"Error writing main file: {e}")
        return False

if __name__ == "__main__":
    print("Embedding SVG radio station icons into HTML...")
    print("=" * 50)
    
    success = update_radio_icons_in_html()
    
    if success:
        print("\n🎉 All done! The radio station icons should now display properly.")
        print("You can test the application to verify the icons are working.")
    else:
        print("\n❌ Something went wrong. Please check the error messages above.")
