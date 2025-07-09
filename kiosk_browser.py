#!/usr/bin/env python3
"""
Office Kiosk Browser Application - Qt6 Version
A touchscreen-friendly browser with shortcuts for Home Assistant, YouTube Music, Radio Browser, and Google.
Designed for Raspberry Pi but works on Windows for testing.
Upgraded to Qt6 for better modern web compatibility.
"""

import sys
import logging
import subprocess
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFrame, QMessageBox, QLabel)

# Try to import WebEngine
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
    WEBENGINE_AVAILABLE = True
    logging.info("Using Qt6 QtWebEngine for web rendering")
except ImportError:
    logging.error("Qt6 WebEngine not available - please install PyQt6-WebEngine")
    WEBENGINE_AVAILABLE = False
    # Create a minimal placeholder
    class QWebEngineView(QWidget):
        def __init__(self):
            super().__init__()
        def setHtml(self, html):
            pass
        def load(self, url):
            pass
        def back(self):
            pass
        def forward(self):
            pass
        def reload(self):
            pass
    class QWebEngineSettings:
        pass
    class QWebEngineProfile:
        pass

from PyQt6.QtCore import QUrl, Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter
from PyQt6.QtSvgWidgets import QSvgWidget

# Try to import SVG support for Qt6
try:
    from PyQt6.QtSvg import QSvgRenderer
    SVG_AVAILABLE = True
    logging.info("Qt6 SVG support available")
except ImportError:
    logging.warning("Qt6 SVG support not available - SVG icons may not display")
    SVG_AVAILABLE = False
    QSvgRenderer = None

from version import get_version_string, get_full_version_info

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class KioskBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Log version information
        version_info = get_full_version_info()
        logging.info(f"Starting Office Kiosk Browser {version_info['formatted']} - Qt6 Version")
        
        self.web_view = None  # Initialize early
        self.is_raspberry_pi = self.detect_raspberry_pi()
        self.keyboard_visible = False  # Track virtual keyboard state
        self.keyboard_temp_windowed = False  # Track if we temporarily exited fullscreen for keyboard
        self.setup_ui()
        self.setup_web_view()
        self.load_home_page()
        
    def detect_raspberry_pi(self):
        """Detect if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'Raspberry Pi' in cpuinfo
        except (FileNotFoundError, PermissionError):
            return False
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Office Kiosk Browser - Qt6")
        
        # Set window size optimized for 1024x600 displays (Waveshare touchscreen)
        if self.is_raspberry_pi:
            # For Raspberry Pi with 1024x600 touchscreen - fit exactly
            self.setGeometry(0, 0, 1024, 600)
            # Debug keyboard environment on Pi
            self.debug_keyboard_environment()
        else:
            # For development on Windows - use smaller size to match Pi resolution
            self.setGeometry(100, 100, 1024, 600)
        
        # Set up the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create web view first
        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
        else:
            self.web_view = QWebEngineView()  # Placeholder when WebEngine not available
            # Show error message
            error_label = QLabel("Qt6 WebEngine not available. Please install PyQt6-WebEngine package.")
            error_label.setStyleSheet("color: red; font-weight: bold; padding: 20px;")
            main_layout.addWidget(error_label)
        
        # Create control panel
        self.create_control_panel(main_layout)
        
        # Add web view to layout
        main_layout.addWidget(self.web_view)
        
        # Set style for touch-friendly interface
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                color: white;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                margin: 1px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QFrame {
                background-color: #34495e;
                border-radius: 10px;
                margin: 5px;
            }
        """)
        
    def load_icon(self, icon_name):
        """Load an SVG icon from the icons directory with Qt6 SVG support"""
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', f'{icon_name}.svg')
        if os.path.exists(icon_path):
            if SVG_AVAILABLE:
                # Use SVG renderer to create a pixmap for the icon
                renderer = QSvgRenderer(icon_path)
                if renderer.isValid():
                    # Create a pixmap to render the SVG into
                    pixmap = QPixmap(64, 64)  # Standard icon size
                    pixmap.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    
                    return QIcon(pixmap)
                else:
                    logging.warning(f"Invalid SVG file: {icon_path}")
                    return self.create_fallback_icon(icon_name)
            else:
                # Fallback: try direct QIcon loading (may not work for SVG in Qt6)
                icon = QIcon(icon_path)
                if icon.isNull():
                    logging.warning(f"SVG icon could not be loaded (Qt6 SVG not available): {icon_path}")
                    return self.create_fallback_icon(icon_name)
                return icon
        else:
            logging.warning(f"Icon not found: {icon_path}")
            return self.create_fallback_icon(icon_name)
    
    def create_fallback_icon(self, icon_name):
        """Create a simple text-based fallback icon when SVG is not available"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.white)
        
        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.black)
        font = QFont()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        
        # Map icon names to simple text fallbacks
        fallback_text = {
            'back': '←',
            'forward': '→',
            'refresh': '↻',
            'home': '🏠',
            'homeassistant': 'HA',
            'google': 'G',
            'youtube': 'YT',
            'music': '♪',
            'radio': '📻',
            'fullscreen': '⛶',
            'keyboard': '⌨',
            'shutdown': '⏻'
        }
        
        text = fallback_text.get(icon_name, icon_name[:2].upper())
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        
        return QIcon(pixmap)
        
    def create_control_panel(self, main_layout):
        """Create the control panel with controls on left and shortcuts on right"""
        control_frame = QFrame()
        # Use percentage of window height instead of fixed pixels
        window_height = self.height()
        window_width = self.width()
        control_height = max(120, int(window_height * 0.20))  # 20% of window height, minimum 120px for 2-row layout
        control_frame.setFixedHeight(control_height)
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 5)  # Increased margins
        control_layout.setSpacing(60)  # Increased space between groups
        control_frame.setLayout(control_layout)
        
        # Add version label as a small overlay in the top-left corner
        version_info = get_full_version_info()
        version_label = QLabel(f"{version_info['formatted']} (Qt6)", control_frame)
        version_label.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                font-size: 10px;
                font-weight: normal;
                background-color: rgba(0, 0, 0, 0.3);
                padding: 2px 6px;
                border-radius: 3px;
            }
        """)
        version_label.move(25, 0)  # Position with more spacing from edge
        version_label.adjustSize()  # Resize to fit content
        
        # Left side - Navigation controls group
        nav_controls_group = QFrame()
        # Navigation controls group height - taller for 2-row layout
        nav_width_percent = 0.5 if self.is_raspberry_pi else 0.4  # 50% vs 40% of window width
        nav_height = int(window_height * 0.16)  # 16% of window height for 2-row button layout
        nav_controls_group.setFixedWidth(int(window_width * nav_width_percent))
        nav_controls_group.setFixedHeight(nav_height)
        nav_controls_group.setStyleSheet("""
            QFrame {
                background-color: rgba(44, 62, 80, 0.8);
                border-radius: 15px;
                margin: 2px;
                padding: 5px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        nav_controls_layout = QVBoxLayout()  # Changed to vertical for 2-row layout
        nav_controls_layout.setSpacing(5)  # Reduced spacing for compact 2-row layout
        nav_controls_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins for maximum button space
        nav_controls_group.setLayout(nav_controls_layout)
        
        # Create top and bottom rows for navigation buttons
        nav_top_row = QHBoxLayout()
        nav_bottom_row = QHBoxLayout()
        
        # Adjust spacing based on platform
        if self.is_raspberry_pi:
            nav_top_row.setSpacing(5)  # Reduced spacing for Pi
            nav_bottom_row.setSpacing(5)
        else:
            nav_top_row.setSpacing(10)  # Standard spacing
            nav_bottom_row.setSpacing(10)
        
        # Navigation buttons - consistent sizing with proportional fonts for 2-row layout
        if self.is_raspberry_pi:
            font_size = max(10, int(control_height * 0.04))  # Smaller font for Pi's compact layout
        else:
            font_size = max(14, int(control_height * 0.06))  # Standard font size
            
        nav_button_style = f"""
            QPushButton {{
                background-color: #3498db;
                border: none;
                color: white;
                font-size: {font_size}px;
                font-weight: bold;
                border-radius: 8px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QPushButton:pressed {{
                background-color: #21618c;
            }}
            QPushButton:disabled {{
                background-color: #7f8c8d;
                color: #bdc3c7;
            }}
        """
        
        # Create navigation buttons with proportional size for 2-row layout
        # Button size based on available space in 2 rows - Pi optimized
        nav_available_width = int(window_width * nav_width_percent) - 20  # Account for margins
        
        if self.is_raspberry_pi:
            # Smaller buttons for Pi's compact screen (typically 1024x600)
            button_width = min(80, int(nav_available_width / 3.2))  # Slightly more space between buttons
            button_height = min(50, int(nav_height / 2.5))  # Smaller height to prevent overlap
        else:
            # Standard sizing for larger screens
            button_width = int(nav_available_width / 3)  # 3 buttons per row
            button_height = int((nav_height - 20) / 2)  # 2 rows, account for margins
            
        button_size = (button_width, button_height)
        
        # Debug info for Pi sizing
        if self.is_raspberry_pi:
            logging.info(f"Pi button sizing: window={window_width}x{window_height}, nav_width={int(window_width * nav_width_percent)}, button={button_width}x{button_height}")
        
        # Determine icon size based on platform
        if self.is_raspberry_pi:
            icon_size_ratio = 0.35  # Slightly larger icons for small Pi buttons
        else:
            icon_size_ratio = 0.25  # Standard icon size
            
        icon_size = QSize(int(button_width * icon_size_ratio), int(button_height * icon_size_ratio))
        
        self.back_btn = QPushButton()
        self.back_btn.setIcon(self.load_icon('back'))
        self.back_btn.setIconSize(icon_size)
        self.back_btn.clicked.connect(self.web_view.back)
        self.back_btn.setFixedSize(*button_size)
        self.back_btn.setStyleSheet(nav_button_style)
        self.back_btn.setToolTip("Go Back")
        
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(self.load_icon('forward'))
        self.forward_btn.setIconSize(icon_size)
        self.forward_btn.clicked.connect(self.web_view.forward)
        self.forward_btn.setFixedSize(*button_size)
        self.forward_btn.setStyleSheet(nav_button_style)
        self.forward_btn.setToolTip("Go Forward")
        
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(self.load_icon('refresh'))
        self.refresh_btn.setIconSize(icon_size)
        self.refresh_btn.clicked.connect(self.web_view.reload)
        self.refresh_btn.setFixedSize(*button_size)
        self.refresh_btn.setStyleSheet(nav_button_style)
        self.refresh_btn.setToolTip("Refresh Page")
        
        self.home_btn = QPushButton()
        self.home_btn.setIcon(self.load_icon('home'))
        self.home_btn.setIconSize(icon_size)
        self.home_btn.clicked.connect(self.load_home_page)
        self.home_btn.setFixedSize(*button_size)
        self.home_btn.setStyleSheet(nav_button_style)
        self.home_btn.setToolTip("Go Home")
        
        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.setIcon(self.load_icon('fullscreen'))
        self.fullscreen_btn.setIconSize(icon_size)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setFixedSize(*button_size)
        self.fullscreen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #9b59b6;
                border: none;
                color: white;
                font-size: {max(16, int(font_size * 1.1))}px;
                font-weight: bold;
                border-radius: 8px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: #8e44ad;
            }}
            QPushButton:pressed {{
                background-color: #732d91;
            }}
        """)
        self.fullscreen_btn.setToolTip("Toggle Fullscreen")
        
        # Arrange buttons in 2 rows: Top row (back, forward, refresh), Bottom row (home, fullscreen, shutdown if Pi)
        nav_top_row.addWidget(self.back_btn)
        nav_top_row.addWidget(self.forward_btn)
        nav_top_row.addWidget(self.refresh_btn)
        
        nav_bottom_row.addWidget(self.home_btn)
        nav_bottom_row.addWidget(self.fullscreen_btn)
        
        # Add Pi-specific buttons only on Raspberry Pi
        if self.is_raspberry_pi:
            # Virtual keyboard toggle button
            self.keyboard_btn = QPushButton()
            self.keyboard_btn.setIcon(self.load_icon('keyboard'))
            self.keyboard_btn.setIconSize(icon_size)
            self.keyboard_btn.clicked.connect(self.toggle_virtual_keyboard)
            self.keyboard_btn.setFixedSize(*button_size)
            self.keyboard_visible = False  # Track keyboard state
            self.update_keyboard_button_style()
            self.keyboard_btn.setToolTip("Toggle Virtual Keyboard")
            nav_bottom_row.addWidget(self.keyboard_btn)
            
            # Shutdown button
            self.shutdown_btn = QPushButton()
            self.shutdown_btn.setIcon(self.load_icon('shutdown'))
            self.shutdown_btn.setIconSize(icon_size)
            self.shutdown_btn.clicked.connect(self.shutdown_pi)
            self.shutdown_btn.setFixedSize(*button_size)
            self.shutdown_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #e74c3c;
                    border: none;
                    color: white;
                    font-size: {max(12, int(font_size * 0.9))}px;
                    font-weight: bold;
                    border-radius: 8px;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: #c0392b;
                }}
                QPushButton:pressed {{
                    background-color: #a93226;
                }}
            """)
            self.shutdown_btn.setToolTip("Shutdown Raspberry Pi")
            nav_bottom_row.addWidget(self.shutdown_btn)
            logging.info("Raspberry Pi detected - keyboard and shutdown buttons added")
        
        # Add the two rows to the main navigation layout
        nav_controls_layout.addLayout(nav_top_row)
        nav_controls_layout.addLayout(nav_bottom_row)
        
        # Right side - Shortcuts group
        shortcuts_group = QFrame()
        shortcuts_group.setStyleSheet("""
            QFrame {
                background-color: rgba(44, 62, 80, 0.8);
                border-radius: 15px;
                margin: 2px;
                padding: 5px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        shortcuts_layout = QVBoxLayout()  # Changed to vertical for 2-row layout
        shortcuts_layout.setSpacing(5)  # Reduced spacing for compact 2-row layout
        shortcuts_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins for maximum button space
        shortcuts_group.setLayout(shortcuts_layout)
        
        # Create top and bottom rows for shortcut buttons
        shortcuts_top_row = QHBoxLayout()
        shortcuts_bottom_row = QHBoxLayout()
        shortcuts_top_row.setSpacing(10)
        shortcuts_bottom_row.setSpacing(10)
        
        # Define shortcuts with their URLs and icon names - arranged for 3x2 grid
        shortcuts = [
            ("HOME ASST", "http://homeassistant.local:8123", "#e74c3c", "homeassistant"),
            ("YT MUSIC", "https://music.youtube.com", "#e67e22", "music"),
            ("RADIO", "https://www.radio-browser.info", "#9b59b6", "radio"),
            ("GOOGLE", "https://www.google.com", "#27ae60", "google"),
            ("YOUTUBE", "https://www.youtube.com", "#c0392b", "youtube")
        ]
        
        # Calculate shortcut button dimensions for 3x2 grid
        shortcuts_width = int(window_width * 0.35)  # Available width for shortcuts
        shortcut_button_width = int((shortcuts_width - 40) / 3)  # 3 buttons per top row, account for margins
        shortcut_button_height = int((nav_height - 30) / 2)  # Same height as nav section, 2 rows
        shortcut_font_size = max(8, int(control_height * 0.06))  # Smaller font for icon+text buttons
        
        self.shortcut_buttons = []
        for i, (name, url, color, icon_name) in enumerate(shortcuts):
            btn = QPushButton(name)
            btn.setIcon(self.load_icon(icon_name))
            btn.setIconSize(QSize(int(shortcut_button_width * 0.3), int(shortcut_button_height * 0.3)))
            btn.setFixedSize(shortcut_button_width, shortcut_button_height)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: none;
                    color: white;
                    padding: 4px;
                    font-size: {shortcut_font_size}px;
                    font-weight: bold;
                    border-radius: 8px;
                    margin: 2px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {self.darken_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(self.darken_color(color))};
                }}
            """)
            btn.clicked.connect(lambda checked, u=url: self.load_url(u))
            btn.setToolTip(f"Open {name}")
            
            # Add to appropriate row (0,1,2 = top row, 3,4 = bottom row)
            if i < 3:
                shortcuts_top_row.addWidget(btn)
            else:
                shortcuts_bottom_row.addWidget(btn)
            
            self.shortcut_buttons.append(btn)
        
        # Add the two rows to the shortcuts layout
        shortcuts_layout.addLayout(shortcuts_top_row)
        shortcuts_layout.addLayout(shortcuts_bottom_row)
        
        # Add groups to main layout
        control_layout.addWidget(nav_controls_group)
        control_layout.addStretch()  # This creates flexible space between groups
        control_layout.addWidget(shortcuts_group)
        
        main_layout.addWidget(control_frame)
        
    def darken_color(self, hex_color):
        """Darken a hex color for hover effects"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * 0.8)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def setup_web_view(self):
        """Configure the web view settings with Qt6 enhancements"""
        if not WEBENGINE_AVAILABLE:
            logging.warning("WebEngine not available - web functionality limited")
            return
            
        # Qt6 WebEngine has better modern web support by default
        settings = self.web_view.settings()
        
        # Enhanced settings for Qt6
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        
        # Qt6 WebEngine profile for modern compatibility
        profile = self.web_view.page().profile()
        
        # Set a modern user agent that YouTube will accept
        modern_user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        profile.setHttpUserAgent(modern_user_agent)
        logging.info(f"Set modern user agent: {modern_user_agent}")
        
        # Additional optimizations for Raspberry Pi
        if self.is_raspberry_pi:
            # More conservative settings for Pi
            settings.setAttribute(QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, False)
            logging.info("Applied Raspberry Pi specific Qt6 WebEngine settings")
        
        # Connect URL change signal
        self.web_view.urlChanged.connect(self.on_url_changed)
        
        # Connect loading signals
        if hasattr(self.web_view, 'loadStarted'):
            self.web_view.loadStarted.connect(self.on_load_started)
        if hasattr(self.web_view, 'loadFinished'):
            self.web_view.loadFinished.connect(self.on_load_finished)
        if hasattr(self.web_view, 'loadProgress'):
            self.web_view.loadProgress.connect(self.on_load_progress)
        
        logging.info("Qt6 WebEngine setup complete with modern compatibility")
        
    def load_home_page(self):
        """Load the default home page"""
        if not WEBENGINE_AVAILABLE:
            return
            
        # Create a simple HTML home page
        home_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Office Kiosk - Home (Qt6)</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 50px;
                    margin: 0;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                }
                h1 {
                    font-size: 3em;
                    margin-bottom: 20px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                .version {
                    font-size: 1.2em;
                    margin-bottom: 30px;
                    opacity: 0.8;
                    color: #a8e6cf;
                }
                .welcome {
                    font-size: 1.5em;
                    margin-bottom: 40px;
                    opacity: 0.9;
                }
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 40px;
                }
                .feature-card {
                    background: rgba(255,255,255,0.1);
                    border-radius: 15px;
                    padding: 25px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                    transition: transform 0.3s ease;
                }
                .feature-card:hover {
                    transform: translateY(-5px);
                }
                .feature-card h3 {
                    margin-bottom: 15px;
                    color: #a8e6cf;
                }
                .time {
                    font-size: 2em;
                    margin-top: 30px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🖥️ OFFICE KIOSK</h1>
                <div class="version">✨ Powered by Qt6 - Modern Web Support ✨</div>
                <div class="welcome">Welcome! Use the shortcuts above to navigate to your favorite services.</div>
                <div class="time" id="current-time"></div>
                
                <div class="features">
                    <div class="feature-card">
                        <h3>🏠 HOME ASSISTANT</h3>
                        <p>Control your smart home devices and automations with modern interface support</p>
                    </div>
                    <div class="feature-card">
                        <h3>🎵 YOUTUBE MUSIC</h3>
                        <p>Stream music with full YouTube compatibility - no more "outdated browser" errors!</p>
                    </div>
                    <div class="feature-card">
                        <h3>🔍 GOOGLE SEARCH</h3>
                        <p>Search the web with full modern browser support and enhanced performance</p>
                    </div>
                    <div class="feature-card">
                        <h3>📺 YOUTUBE</h3>
                        <p>Watch videos with improved video codec support and better performance</p>
                    </div>
                </div>
            </div>
            
            <script>
                function updateTime() {
                    const now = new Date();
                    const timeString = now.toLocaleTimeString('en-US', {
                        hour12: true,
                        hour: 'numeric',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    const dateString = now.toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    });
                    document.getElementById('current-time').innerHTML = 
                        `${timeString}<br><small style="font-size: 0.6em;">${dateString}</small>`;
                }
                
                updateTime();
                setInterval(updateTime, 1000);
                
                // Add some Qt6 feature detection
                console.log('Qt6 Kiosk Browser loaded successfully');
            </script>
        </body>
        </html>
        """
        
        self.web_view.setHtml(home_html)
        
    def load_url(self, url):
        """Load a specific URL with Qt6 enhancements"""
        if not WEBENGINE_AVAILABLE:
            QMessageBox.warning(self, "WebEngine Not Available", 
                              "Qt6 WebEngine is not installed. Please install PyQt6-WebEngine.")
            return
            
        try:
            logging.info(f"Attempting to load URL: {url}")
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                logging.info(f"Modified URL to: {url}")
            
            qurl = QUrl(url)
            if not qurl.isValid():
                logging.error(f"Invalid URL: {url}")
                QMessageBox.warning(self, "Invalid URL", f"The URL '{url}' is not valid.")
                return
                
            logging.info(f"Loading URL: {qurl.toString()}")
            self.web_view.load(qurl)
        except Exception as e:
            logging.error(f"Error loading URL {url}: {str(e)}")
            QMessageBox.critical(self, "Load Error", f"Failed to load URL: {str(e)}")
        
    def on_url_changed(self, url):
        """Update address bar when URL changes"""
        logging.info(f"URL changed to: {url.toString()}")
        
    def on_load_started(self):
        """Called when page starts loading"""
        logging.info("Page load started")
        # Visual feedback via style change
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f39c12;
                border: none;
                color: white;
                font-size: {14}px;
                font-weight: bold;
                border-radius: 8px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: #e67e22;
            }}
            QPushButton:pressed {{
                background-color: #d35400;
            }}
        """)
        
    def on_load_finished(self, success):
        """Called when page finishes loading"""
        current_url = self.web_view.url().toString()
        if success:
            logging.info(f"Page loaded successfully: {current_url}")
        else:
            logging.error(f"Page failed to load: {current_url}")
            
        # Reset refresh button to normal style
        font_size = max(14, int(self.height() * 0.20 * 0.06))  # Recalculate font size
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498db;
                border: none;
                color: white;
                font-size: {font_size}px;
                font-weight: bold;
                border-radius: 8px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QPushButton:pressed {{
                background-color: #21618c;
            }}
            QPushButton:disabled {{
                background-color: #7f8c8d;
                color: #bdc3c7;
            }}
        """)
        
        if not success:
            # Handle specific error cases
            if "homeassistant" in current_url.lower():
                self.handle_network_error(current_url)
            else:
                QMessageBox.warning(self, "Load Error", f"Failed to load the page: {current_url}")
                
    def on_load_progress(self, progress):
        """Called during page loading to show progress"""
        logging.debug(f"Load progress: {progress}%")
        # Visual feedback through button color intensity
        if progress < 100:
            # Gradually change color from orange to green as loading progresses
            red_val = max(100, 243 - int(progress * 1.4))  # Start orange, get greener
            green_val = min(255, 156 + int(progress * 1.0))  # Start orange, get greener
            blue_val = 18  # Keep blue component low for orange-green transition
            
            self.refresh_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgb({red_val}, {green_val}, {blue_val});
                    border: none;
                    color: white;
                    font-size: {14}px;
                    font-weight: bold;
                    border-radius: 8px;
                    margin: 2px;
                }}
            """)
            
    def handle_network_error(self, url):
        """Handle network connectivity issues"""
        logging.warning(f"Network error for URL: {url}")
        
        # Check if it's a local Home Assistant URL
        if "homeassistant.local" in url or "192.168." in url or "10." in url or "127.0.0.1" in url:
            # Suggest troubleshooting steps for local network
            error_msg = f"""
Failed to connect to Home Assistant at {url}

Possible solutions:
1. Check if Home Assistant is running
2. Verify the IP address/hostname
3. Check if port 8123 is accessible
4. Try accessing {url} in a regular browser first
5. If using HTTPS, try HTTP instead (SSL certificate issues)

Qt6 WebEngine provides better SSL/TLS support than Qt5.
            """
            QMessageBox.warning(self, "Home Assistant Connection Error", error_msg)
        else:
            QMessageBox.warning(self, "Network Error", f"Failed to connect to {url}")
            
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def toggle_virtual_keyboard(self):
        """Toggle the virtual keyboard (wvkbd) on Raspberry Pi"""
        if not self.is_raspberry_pi:
            QMessageBox.warning(self, "Not Available", "Virtual keyboard is only available on Raspberry Pi.")
            return
        
        try:
            # Check if wvkbd is installed first
            result = subprocess.run(['which', 'wvkbd-mobintl'], capture_output=True, text=True)
            if result.returncode != 0:
                self.show_keyboard_install_dialog()
                return
            
            # Check if keyboard is actually running
            result = subprocess.run(['pgrep', 'wvkbd-mobintl'], capture_output=True, text=True)
            keyboard_running = result.returncode == 0
            
            if keyboard_running:
                # Hide keyboard
                logging.info("Hiding virtual keyboard (wvkbd)")
                subprocess.run(['pkill', 'wvkbd-mobintl'], check=False)
                self.keyboard_visible = False
                
                # Restore fullscreen if we temporarily exited for keyboard visibility
                if self.keyboard_temp_windowed:
                    logging.info("Restoring fullscreen mode after hiding keyboard")
                    self.showFullScreen()
                    self.keyboard_temp_windowed = False
            else:
                # Show keyboard - try different methods for Wayland compatibility
                logging.info("Showing virtual keyboard (wvkbd) on Wayland")
                
                # Detect if we're on Wayland
                wayland_display = os.environ.get('WAYLAND_DISPLAY')
                xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
                is_wayland = wayland_display or xdg_session_type == 'wayland'
                
                if is_wayland:
                    # Wayland-optimized command with overlay layer to appear above fullscreen apps
                    cmd = [
                        'wvkbd-mobintl',
                        '-L', '300',  # Landscape mode with height
                        '--bg', '333333cc',  # Semi-transparent dark background
                        '--fg', 'ffffff',     # White text
                        '--layer', 'overlay'  # Use overlay layer to appear above fullscreen apps
                    ]
                    logging.info("Using Wayland-optimized wvkbd settings with overlay layer")
                else:
                    # X11 fallback
                    cmd = [
                        'wvkbd-mobintl',
                        '-L', '280',  # Landscape mode with height
                        '--fg', 'white'
                    ]
                    logging.info("Using X11 wvkbd settings")
                
                # Start keyboard process
                try:
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # Quick check if process started successfully
                    time.sleep(0.1)
                    if process.poll() is not None:
                        # Process died immediately, try basic fallback
                        logging.warning("Landscape mode failed, trying basic wvkbd")
                        process = subprocess.Popen(['wvkbd-mobintl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        # If we're in fullscreen and keyboard fails to overlay, temporarily exit fullscreen
                        if self.isFullScreen():
                            logging.info("Temporarily exiting fullscreen for virtual keyboard visibility")
                            self.showNormal()
                            self.keyboard_temp_windowed = True
                        
                except Exception as e:
                    logging.error(f"Failed to start wvkbd: {e}")
                    # Try absolute basic fallback
                    process = subprocess.Popen(['wvkbd-mobintl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # If we're in fullscreen, temporarily exit for keyboard visibility
                    if self.isFullScreen():
                        logging.info("Temporarily exiting fullscreen for virtual keyboard visibility")
                        self.showNormal()
                        self.keyboard_temp_windowed = True
                
                # Give it a moment to start and check if it's actually running
                QTimer.singleShot(500, lambda: self.verify_keyboard_started(process))
                self.keyboard_visible = True
            
            # Update button appearance
            self.update_keyboard_button_style()
            
        except FileNotFoundError:
            # wvkbd not installed
            logging.error("wvkbd not found - virtual keyboard not available")
            QMessageBox.warning(
                self,
                "Virtual Keyboard Not Available",
                "wvkbd (virtual keyboard) is not installed.\n\n"
                "To install it:\n"
                "sudo apt update\n"
                "sudo apt install wvkbd"
            )
        except Exception as e:
            logging.error(f"Error toggling virtual keyboard: {e}")
            QMessageBox.warning(self, "Keyboard Error", f"Failed to toggle virtual keyboard: {e}")
    
    def show_keyboard_install_dialog(self):
        """Show dialog with instructions to install wvkbd"""
        QMessageBox.information(
            self,
            "Virtual Keyboard Not Installed",
            "wvkbd (virtual keyboard) is not installed.\n\n"
            "To install it:\n"
            "sudo apt update\n"
            "sudo apt install wvkbd\n\n"
            "Or run the quick install script:\n"
            "./install/quick_install_pyqt6.sh"
        )
    
    def verify_keyboard_started(self, process):
        """Verify that the keyboard process started successfully"""
        try:
            # Check if process is still running
            if process.poll() is None:
                # Process is running, check if we can find it
                result = subprocess.run(['pgrep', 'wvkbd-mobintl'], capture_output=True, text=True)
                if result.returncode == 0:
                    logging.info("Virtual keyboard started successfully")
                    self.ensure_keyboard_visible()
                else:
                    logging.warning("Keyboard process started but not found in process list")
                    self.keyboard_visible = False
            else:
                # Process died, check stderr for errors
                _, stderr = process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"
                logging.error(f"Keyboard process failed to start: {error_msg}")
                self.keyboard_visible = False
                
                # Show user-friendly error message
                QMessageBox.warning(
                    self,
                    "Keyboard Failed to Start",
                    f"The virtual keyboard failed to start.\n\n"
                    f"This may be because:\n"
                    f"• Wayland compositor doesn't support virtual keyboards\n"
                    f"• wvkbd needs additional permissions\n"
                    f"• Display server issues\n\n"
                    f"Try running manually: wvkbd-mobintl -L"
                )
        except Exception as e:
            logging.error(f"Error verifying keyboard start: {e}")
            self.keyboard_visible = False
        
        # Update button style regardless
        self.update_keyboard_button_style()
    
    def ensure_keyboard_visible(self):
        """Ensure the virtual keyboard is visible and on top"""
        try:
            # On Wayland, window management is handled by the compositor
            wayland_display = os.environ.get('WAYLAND_DISPLAY')
            xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
            is_wayland = wayland_display or xdg_session_type == 'wayland'
            
            if is_wayland:
                # On Wayland, we can't directly manipulate windows, but we can try some tricks
                logging.info("Wayland detected - keyboard window management handled by compositor")
                # Give focus back to browser after keyboard starts
                self.activateWindow()
                self.raise_()
            else:
                # On X11, try traditional window management
                try:
                    subprocess.run(['wmctrl', '-a', 'wvkbd'], check=False)
                except FileNotFoundError:
                    # wmctrl not available, that's okay
                    pass
        except Exception as e:
            logging.debug(f"Could not manage keyboard window: {e}")
    
    def debug_keyboard_environment(self):
        """Debug information about keyboard environment"""
        logging.info("=== Keyboard Environment Debug ===")
        logging.info(f"XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', 'not set')}")
        logging.info(f"WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'not set')}")
        logging.info(f"DISPLAY: {os.environ.get('DISPLAY', 'not set')}")
        
        # Check if wvkbd is available
        result = subprocess.run(['which', 'wvkbd-mobintl'], capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"wvkbd-mobintl found at: {result.stdout.strip()}")
            
            # Try to get version info
            version_result = subprocess.run(['wvkbd-mobintl', '--help'], capture_output=True, text=True)
            if version_result.returncode == 0:
                logging.info("wvkbd help output available")
            else:
                logging.warning("Could not get wvkbd help/version")
        else:
            logging.error("wvkbd-mobintl not found in PATH")
        
        # Check for alternative keyboards
        for kb in ['onboard', 'florence', 'squeekboard']:
            result = subprocess.run(['which', kb], capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Alternative keyboard found: {kb}")
        
        logging.info("=== End Keyboard Debug ===")
    
    def update_keyboard_button_style(self):
        """Update the keyboard button style based on current state"""
        if not hasattr(self, 'keyboard_btn'):
            return
        
        # Get the current font size from the nav buttons
        font_size = max(14, int(self.height() * 0.06))
        
        if self.keyboard_visible:
            # Keyboard is visible - show as active
            style = f"""
                QPushButton {{
                    background-color: #f39c12;
                    border: none;
                    color: white;
                    font-size: {max(12, int(font_size * 0.9))}px;
                    font-weight: bold;
                    border-radius: 8px;
                    margin: 2px;
                    border: 2px solid #e67e22;
                }}
                QPushButton:hover {{
                    background-color: #e67e22;
                }}
                QPushButton:pressed {{
                    background-color: #d68910;
                }}
            """
            self.keyboard_btn.setToolTip("Hide Virtual Keyboard")
        else:
            # Keyboard is hidden - show as inactive
            style = f"""
                QPushButton {{
                    background-color: #95a5a6;
                    border: none;
                    color: white;
                    font-size: {max(12, int(font_size * 0.9))}px;
                    font-weight: bold;
                    border-radius: 8px;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: #7f8c8d;
                }}
                QPushButton:pressed {{
                    background-color: #6c7b7d;
                }}
            """
            self.keyboard_btn.setToolTip("Show Virtual Keyboard")
        
        self.keyboard_btn.setStyleSheet(style)
            
    def shutdown_pi(self):
        """Safely shutdown the Raspberry Pi"""
        if not self.is_raspberry_pi:
            QMessageBox.warning(self, "Not Available", "Shutdown button is only available on Raspberry Pi.")
            return
            
        reply = QMessageBox.question(
            self,
            "Shutdown Raspberry Pi",
            "Are you sure you want to shutdown the Raspberry Pi?\n\nThis will turn off the device completely.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logging.info("User initiated Raspberry Pi shutdown")
            try:
                # Show a final message
                QMessageBox.information(
                    self,
                    "Shutting Down",
                    "The Raspberry Pi will shutdown now.\nPlease wait for the activity LED to stop blinking before unplugging power."
                )
                
                # Close the application gracefully
                self.close()
                
                # Execute shutdown command
                subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
                
            except subprocess.CalledProcessError as e:
                logging.error(f"Shutdown command failed: {e}")
                QMessageBox.critical(
                    self,
                    "Shutdown Failed",
                    f"Failed to shutdown the Raspberry Pi.\nError: {e}\n\nYou may need to configure sudo permissions for shutdown."
                )
            except Exception as e:
                logging.error(f"Unexpected error during shutdown: {e}")
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
            
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        elif event.key() == Qt.Key.Key_F12:
            # Toggle dev tools for debugging
            self.toggle_dev_tools()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_R:
                self.web_view.reload()
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Clean up when the application is closing"""
        if self.is_raspberry_pi and hasattr(self, 'keyboard_visible') and self.keyboard_visible:
            # Hide virtual keyboard when closing
            logging.info("Hiding virtual keyboard on application close")
            try:
                subprocess.run(['pkill', 'wvkbd-mobintl'], check=False)
            except Exception as e:
                logging.warning(f"Could not hide virtual keyboard on close: {e}")
        
        # Call parent closeEvent to ensure proper cleanup
        super().closeEvent(event)
        
    def toggle_dev_tools(self):
        """Toggle developer tools for debugging"""
        if not WEBENGINE_AVAILABLE:
            return
            
        try:
            page = self.web_view.page()
            if hasattr(page, 'setDevToolsPage'):
                logging.info("Opening developer tools")
                dev_tools = QWebEngineView()
                page.setDevToolsPage(dev_tools.page())
                dev_tools.show()
            else:
                logging.warning("Developer tools not available")
        except Exception as e:
            logging.error(f"Error opening developer tools: {e}")

def main():
    """Main function to run the application"""
    # Set Qt application attributes before creating QApplication
    # Note: In Qt6, high DPI scaling is enabled by default
    # Many Qt5 attributes are no longer needed or have different names in Qt6
    try:
        # These attributes may not exist in Qt6, so we'll try them safely
        if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        if hasattr(Qt.ApplicationAttribute, 'AA_DisableWindowContextHelpButton'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableWindowContextHelpButton, True)
    except AttributeError:
        # Qt6 doesn't need these attributes
        pass
    
    # For Raspberry Pi, add specific attributes
    is_rpi = 'raspberry' in os.uname().machine.lower() if hasattr(os, 'uname') else False
    if is_rpi:
        # Qt6 WebEngine flags for better YouTube compatibility
        chromium_flags = [
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            '--enable-gpu-rasterization',
            '--ignore-gpu-blacklist',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--enable-features=VaapiVideoDecoder',
            '--use-gl=egl',
            '--enable-accelerated-video-decode',
            '--enable-accelerated-mjpeg-decode'
        ]
        os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', ' '.join(chromium_flags))
        logging.info(f"Set Qt6 Chromium flags for Pi: {' '.join(chromium_flags)}")
    else:
        # For development/Windows - enable modern features
        os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', 
            '--enable-features=VaapiVideoDecoder --enable-accelerated-video-decode')
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Office Kiosk Browser Qt6")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Office Kiosk")
    
    # Create and show the main window
    browser = KioskBrowser()
    
    # Check if we should start in fullscreen (useful for Raspberry Pi)
    should_fullscreen = False
    if len(sys.argv) > 1 and '--fullscreen' in sys.argv:
        should_fullscreen = True
    elif is_rpi:
        # Auto-fullscreen on Raspberry Pi
        should_fullscreen = True
        logging.info("Raspberry Pi detected - enabling fullscreen mode")
    
    if should_fullscreen:
        browser.showFullScreen()
        logging.info("Started in fullscreen mode")
    else:
        browser.show()
        logging.info("Started in windowed mode")
    
    # Start the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
