#!/usr/bin/env python3
"""
Test script to verify Qt6 SVG icon support
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter

# Try to import SVG support
try:
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtSvgWidgets import QSvgWidget
    SVG_AVAILABLE = True
    print("✅ Qt6 SVG support available")
except ImportError as e:
    SVG_AVAILABLE = False
    print(f"❌ Qt6 SVG support not available: {e}")
    QSvgRenderer = None

class SVGTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt6 SVG Icon Test")
        self.setGeometry(100, 100, 800, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Status label
        status_text = "✅ SVG Support Available" if SVG_AVAILABLE else "❌ SVG Support Not Available"
        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Test buttons with SVG icons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # List of icons to test
        icons_to_test = ['back', 'forward', 'refresh', 'home', 'homeassistant', 'google', 'youtube', 'keyboard']
        
        for icon_name in icons_to_test:
            button = QPushButton(icon_name.title())
            icon = self.load_svg_icon(icon_name)
            button.setIcon(icon)
            button.setIconSize(QSize(32, 32))
            button.setMinimumSize(100, 60)
            button_layout.addWidget(button)
        
        # Instructions
        instructions = QLabel("If SVG support is working, you should see icons on the buttons above.")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
    def load_svg_icon(self, icon_name):
        """Load SVG icon with fallback"""
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', f'{icon_name}.svg')
        
        if not os.path.exists(icon_path):
            print(f"⚠️  Icon file not found: {icon_path}")
            return self.create_fallback_icon(icon_name)
        
        if SVG_AVAILABLE:
            renderer = QSvgRenderer(icon_path)
            if renderer.isValid():
                pixmap = QPixmap(64, 64)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                print(f"✅ SVG icon loaded: {icon_name}")
                return QIcon(pixmap)
            else:
                print(f"❌ Invalid SVG file: {icon_path}")
                return self.create_fallback_icon(icon_name)
        else:
            # Try direct loading (may not work for SVG in Qt6)
            icon = QIcon(icon_path)
            if icon.isNull():
                print(f"❌ Could not load SVG without Qt6 SVG support: {icon_name}")
                return self.create_fallback_icon(icon_name)
            else:
                print(f"⚠️  SVG loaded without proper support: {icon_name}")
                return icon
    
    def create_fallback_icon(self, icon_name):
        """Create text-based fallback icon"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, icon_name[:2].upper())
        painter.end()
        
        return QIcon(pixmap)

def main():
    app = QApplication(sys.argv)
    
    print("Testing Qt6 SVG Icon Support")
    print("=" * 40)
    
    # Test basic Qt6 imports
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ Qt6 QtWidgets available")
    except ImportError:
        print("❌ Qt6 QtWidgets not available")
        return 1
    
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        print("✅ Qt6 QtWebEngine available")
    except ImportError:
        print("❌ Qt6 QtWebEngine not available")
    
    # Test SVG support
    if SVG_AVAILABLE:
        print("✅ Qt6 QtSvg available")
    else:
        print("❌ Qt6 QtSvg not available")
        print("Install with: sudo apt install python3-pyqt6.qtsvg")
        print("Or with pip: pip3 install PyQt6-Svg")
    
    print("\nLaunching GUI test window...")
    window = SVGTestWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
