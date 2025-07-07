#!/usr/bin/env python3
"""
Icon Test Script
Quick test to verify all SVG icons can be loaded properly.
"""

import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

def load_icon(icon_name):
    """Load an SVG icon from the icons directory"""
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', f'{icon_name}.svg')
    if os.path.exists(icon_path):
        print(f"✓ Found: {icon_path}")
        return QIcon(icon_path)
    else:
        print(f"✗ Missing: {icon_path}")
        return QIcon()

def test_icons():
    """Test all icons in a simple grid"""
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("SVG Icon Test")
    window.setGeometry(100, 100, 600, 400)
    
    layout = QGridLayout()
    
    # Test icons
    icons = [
        ('back', 'Back'),
        ('forward', 'Forward'), 
        ('refresh', 'Refresh'),
        ('home', 'Home'),
        ('fullscreen', 'Fullscreen'),
        ('shutdown', 'Shutdown'),
        ('homeassistant', 'Home Assistant'),
        ('music', 'Music'),
        ('google', 'Google'),
        ('youtube', 'YouTube')
    ]
    
    row = 0
    col = 0
    for icon_name, label in icons:
        btn = QPushButton(label)
        icon = load_icon(icon_name)
        btn.setIcon(icon)
        btn.setIconSize(QSize(32, 32))
        btn.setFixedSize(120, 60)
        
        layout.addWidget(btn, row, col)
        col += 1
        if col >= 4:
            col = 0
            row += 1
    
    window.setLayout(layout)
    window.show()
    
    print("\nIcon test window opened. All icons should be visible.")
    print("Close the window to exit.")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    print("Testing SVG Icons...")
    test_icons()
