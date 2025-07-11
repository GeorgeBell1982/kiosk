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
import tempfile
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
    logging.warning("Qt6 SVG support not available - using fallback icons. Install PyQt6-Qt6 for SVG icon support.")
    SVG_AVAILABLE = False
    QSvgRenderer = None

from version import get_version_string, get_full_version_info

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class KioskBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize early attributes first
        self.web_view = None  # Initialize early
        self.is_raspberry_pi = self.detect_raspberry_pi()
        self.keyboard_visible = False  # Track virtual keyboard state
        self.keyboard_temp_windowed = False  # Track if we temporarily exited fullscreen for keyboard
        
        # Log version information
        version_info = get_full_version_info()
        logging.info(f"Starting Office Kiosk Browser {version_info['formatted']} - Qt6 Version")
        
        # Log automatic update status
        if self.is_raspberry_pi:
            logging.info("Automatic updates are enabled - app will check for and apply updates automatically on startup")
        else:
            logging.info("Running on non-Raspberry Pi system - automatic updates disabled")
        
        self.setup_ui()
        self.setup_web_view()
        self.check_for_updates()  # Check for updates on startup
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
            # Clean up any leftover keyboard processes from previous sessions
            self.cleanup_keyboard_processes()
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
        """Load an SVG icon from the icons directory with Qt6 SVG support and robust fallbacks"""
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', f'{icon_name}.svg')
        
        # Try loading the SVG icon
        if os.path.exists(icon_path):
            if SVG_AVAILABLE:
                try:
                    # Use SVG renderer to create a pixmap for the icon
                    renderer = QSvgRenderer(icon_path)
                    if renderer.isValid():
                        # Create a pixmap to render the SVG into
                        pixmap = QPixmap(64, 64)  # Standard icon size
                        pixmap.fill(Qt.GlobalColor.transparent)
                        
                        painter = QPainter(pixmap)
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                        renderer.render(painter)
                        painter.end()
                        
                        icon = QIcon(pixmap)
                        if not icon.isNull():
                            logging.debug(f"Successfully loaded SVG icon: {icon_name}")
                            return icon
                        else:
                            logging.warning(f"SVG icon rendered but QIcon is null: {icon_path}")
                    else:
                        logging.warning(f"Invalid SVG file: {icon_path}")
                except Exception as e:
                    logging.warning(f"Error rendering SVG icon {icon_name}: {e}")
            else:
                # Try direct QIcon loading (may work for some SVG files)
                try:
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        logging.debug(f"Successfully loaded icon directly: {icon_name}")
                        return icon
                    else:
                        logging.warning(f"SVG icon could not be loaded directly (Qt6 SVG not available): {icon_path}")
                except Exception as e:
                    logging.warning(f"Error loading icon directly {icon_name}: {e}")
        else:
            logging.warning(f"Icon file not found: {icon_path}")
        
        # If we reach here, create a fallback icon
        logging.info(f"Using fallback icon for: {icon_name}")
        return self.create_fallback_icon(icon_name)
    
    def create_fallback_icon(self, icon_name):
        """Create a simple text-based fallback icon when SVG is not available"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create a circular background
        painter.setBrush(Qt.GlobalColor.darkBlue)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawEllipse(4, 4, 56, 56)
        
        # Set font and text color
        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setPixelSize(20)
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
        
        # Enhanced settings for Qt6 with persistent storage
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
        
        # Additional storage settings for login persistence
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        
        # Critical settings for Home Assistant and modern web apps
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, False)
        
        # Enable features needed for service workers and offline functionality
        try:
            # These may not be available in all Qt6 versions
            settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        except AttributeError:
            logging.debug("PdfViewerEnabled not available in this Qt6 version")
        
        # Configure default font sizes for better readability
        settings.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, 14)
        settings.setFontSize(QWebEngineSettings.FontSize.DefaultFixedFontSize, 12)
        settings.setFontSize(QWebEngineSettings.FontSize.MinimumFontSize, 10)
        
        # Qt6 WebEngine profile for modern compatibility
        profile = self.web_view.page().profile()
        
        # Configure persistent storage for Home Assistant login persistence
        data_dir = os.path.expanduser("~/.office_kiosk_data")
        cache_dir = os.path.join(data_dir, "cache")
        downloads_dir = os.path.join(data_dir, "downloads")
        
        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Set persistent storage paths
        profile.setPersistentStoragePath(data_dir)
        profile.setCachePath(cache_dir)
        profile.setDownloadPath(downloads_dir)
        
        # Enable persistent cookies and storage - CRITICAL for Home Assistant login
        from PyQt6.QtWebEngineCore import QWebEngineProfile
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        
        # Configure HTTP cache for better performance and persistence
        from PyQt6.QtWebEngineCore import QWebEngineProfile
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        profile.setHttpCacheMaximumSize(100 * 1024 * 1024)  # 100MB cache
        
        # Set permissions policy for better web app compatibility
        # This is important for Home Assistant's modern web features
        try:
            from PyQt6.QtWebEngineCore import QWebEngineProfile
            # Allow persistent storage by default
            profile.setRequestInterceptor(None)  # Don't intercept requests
        except (AttributeError, ImportError):
            logging.debug("Advanced profile features not available in this Qt6 version")
        
        # Set a modern user agent that Home Assistant will accept
        modern_user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 OfficeKiosk/1.0"
        )
        profile.setHttpUserAgent(modern_user_agent)
        
        # Log configuration details
        logging.info(f"Set modern user agent: {modern_user_agent}")
        logging.info(f"Configured persistent storage at: {data_dir}")
        logging.info(f"Cache directory: {cache_dir}")
        logging.info(f"Downloads directory: {downloads_dir}")
        logging.info(f"Cookies policy: {profile.persistentCookiesPolicy()}")
        logging.info(f"Cache type: {profile.httpCacheType()}")
        logging.info(f"Cache max size: {profile.httpCacheMaximumSize()} bytes")
        
        # Verify storage paths are writable
        try:
            test_file = os.path.join(data_dir, "test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            logging.info("Storage directory is writable")
        except Exception as e:
            logging.error(f"Storage directory is not writable: {e}")
            # Try to use a fallback location
            fallback_dir = os.path.join(tempfile.gettempdir(), "office_kiosk_data")
            os.makedirs(fallback_dir, exist_ok=True)
            profile.setPersistentStoragePath(fallback_dir)
            logging.warning(f"Using fallback storage: {fallback_dir}")
        
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
                .icon {
                    font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", "Times New Roman", serif;
                    font-size: 1.1em;
                    margin-right: 8px;
                    display: inline-block;
                    vertical-align: middle;
                }
                /* Fallback CSS icons if Unicode doesn't work */
                .icon-fallback {
                    display: inline-block;
                    min-width: 24px;
                    height: 24px;
                    margin-right: 8px;
                    background-color: #a8e6cf;
                    border-radius: 50%;
                    vertical-align: middle;
                    text-align: center;
                    line-height: 24px;
                    font-size: 10px;
                    color: #2c3e50;
                    font-weight: bold;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
                .radio-stations {
                    margin-top: 40px;
                    background: rgba(155, 89, 182, 0.1);
                    border-radius: 15px;
                    padding: 25px;
                    border: 1px solid rgba(155, 89, 182, 0.3);
                }
                .radio-stations h2 {
                    color: #a8e6cf;
                    margin-bottom: 20px;
                    font-size: 1.8em;
                }
                .radio-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }
                .radio-link {
                    background: rgba(155, 89, 182, 0.2);
                    border: 1px solid rgba(155, 89, 182, 0.4);
                    border-radius: 10px;
                    padding: 15px;
                    text-decoration: none;
                    color: white;
                    transition: all 0.3s ease;
                    display: block;
                }
                .radio-link:hover {
                    background: rgba(155, 89, 182, 0.3);
                    transform: translateY(-2px);
                    border-color: rgba(155, 89, 182, 0.6);
                }
                .radio-name {
                    font-weight: bold;
                    font-size: 1.1em;
                    margin-bottom: 5px;
                    color: #a8e6cf;
                }
                .radio-icon {
                    width: 24px;
                    height: 24px;
                    margin-right: 8px;
                    vertical-align: middle;
                    border-radius: 50%;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
                .radio-description {
                    font-size: 0.9em;
                    opacity: 0.8;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1><span class="icon" data-fallback="PC">&#x1F4BB;</span> OFFICE KIOSK</h1>
                <div class="version"><span class="icon" data-fallback="★">&#x2728;</span> Powered by Qt6 - Modern Web Support <span class="icon" data-fallback="★">&#x2728;</span></div>
                <div class="welcome">Welcome! Use the shortcuts above to navigate to your favorite services.</div>
                <div class="time" id="current-time"></div>
                
                <div class="radio-stations">
                    <h2><span class="icon" data-fallback="RADIO">&#x1F4FB;</span> Radio Stations</h2>
                    <p style="opacity: 0.8; margin-bottom: 20px;">Quick access to your favorite radio stations</p>
                    <div class="radio-grid">
                        <a href="https://www.radio-browser.info/search?page=1&order=clickcount&reverse=true&hidebroken=true&name=jakaranda" class="radio-link">
                            <div class="radio-name"><img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4gPHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4gPCEtLSBKYWthcmFuZGEgRk0gLSBQdXJwbGUvR3JlZW4gdGhlbWUgLS0+IDxkZWZzPiA8bGluZWFyR3JhZGllbnQgaWQ9Impha2FyYW5kYUdyYWQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPiA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojOEU0NEFEO3N0b3Atb3BhY2l0eToxIiAvPiA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMyN0FFNjA7c3RvcC1vcGFjaXR5OjEiIC8+IDwvbGluZWFyR3JhZGllbnQ+IDwvZGVmcz4gPGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iMzAiIGZpbGw9InVybCgjamFrYXJhbmRhR3JhZCkiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+IDx0ZXh0IHg9IjMyIiB5PSIyNCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkpBSzwvdGV4dD4gPHRleHQgeD0iMzIiIHk9IjQwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTAiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+Rk08L3RleHQ+IDwhLS0gUmFkaW8gd2F2ZXMgLS0+IDxwYXRoIGQ9Ik0gNDUgMjAgUSA1MiAzMiA0NSA0NCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIiBvcGFjaXR5PSIwLjciLz4gPHBhdGggZD0iTSA0OCAyNCBRIDU0IDMyIDQ4IDQwIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgZmlsbD0ibm9uZSIgb3BhY2l0eT0iMC41Ii8+IDwvc3ZnPg==" alt="Jakaranda FM" class="radio-icon"> Jakaranda FM</div>
                            <div class="radio-description">South African community radio station</div>
                        </a>
                        <a href="https://www.radio-browser.info/search?page=1&order=clickcount&reverse=true&hidebroken=true&name=94.7%20Highveld%20Stereo" class="radio-link">
                            <div class="radio-name"><img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4gPHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4gPCEtLSA5NC43IEhpZ2h2ZWxkIFN0ZXJlbyAtLT4gPGRlZnM+IDxsaW5lYXJHcmFkaWVudCBpZD0icmFkaW85NDdHcmFkIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4gPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6I0U3NEMzQztzdG9wLW9wYWNpdHk6MSIgLz4gPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRjM5QzEyO3N0b3Atb3BhY2l0eToxIiAvPiA8L2xpbmVhckdyYWRpZW50PiA8L2RlZnM+IDxjaXJjbGUgY3g9IjMyIiBjeT0iMzIiIHI9IjMwIiBmaWxsPSJ1cmwoI3JhZGlvOTQ3R3JhZCkiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+IDx0ZXh0IHg9IjMyIiB5PSIzOCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPjk0Ljc8L3RleHQ+IDwhLS0gUmFkaW8gd2F2ZXMgLS0+IDxwYXRoIGQ9Ik0gNDUgMjAgUSA1MiAzMiA0NSA0NCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIiBvcGFjaXR5PSIwLjciLz4gPHBhdGggZD0iTSA0OCAyNCBRIDU0IDMyIDQ4IDQwIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgZmlsbD0ibm9uZSIgb3BhY2l0eT0iMC41Ii8+IDwvc3ZnPg==" alt="94.7 Highveld Stereo" class="radio-icon"> 94.7 Highveld Stereo</div>
                            <div class="radio-description">Johannesburg's hit music station</div>
                        </a>
                        <a href="https://www.radio-browser.info/search?page=1&order=clickcount&reverse=true&hidebroken=true&name=KFM%2094.5" class="radio-link">
                            <div class="radio-name"><img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4gPHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4gPCEtLSBLRk0gOTQuNSAtLT4gPGRlZnM+IDxsaW5lYXJHcmFkaWVudCBpZD0icmFkaW9rZm1HcmFkIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4gPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzM0OThEQjtzdG9wLW9wYWNpdHk6MSIgLz4gPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMkVDQzcxO3N0b3Atb3BhY2l0eToxIiAvPiA8L2xpbmVhckdyYWRpZW50PiA8L2RlZnM+IDxjaXJjbGUgY3g9IjMyIiBjeT0iMzIiIHI9IjMwIiBmaWxsPSJ1cmwoI3JhZGlva2ZtR3JhZCkiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+IDx0ZXh0IHg9IjMyIiB5PSIzOCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPks5Rk08L3RleHQ+IDwhLS0gUmFkaW8gd2F2ZXMgLS0+IDxwYXRoIGQ9Ik0gNDUgMjAgUSA1MiAzMiA0NSA0NCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIiBvcGFjaXR5PSIwLjciLz4gPHBhdGggZD0iTSA0OCAyNCBRIDU0IDMyIDQ4IDQwIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgZmlsbD0ibm9uZSIgb3BhY2l0eT0iMC41Ii8+IDwvc3ZnPg==" alt="KFM 94.5" class="radio-icon"> KFM 94.5</div>
                            <div class="radio-description">Cape Town's hit music station</div>
                        </a>
                        <a href="https://www.radio-browser.info/search?page=1&order=clickcount&reverse=true&hidebroken=true&name=Talk%20Radio%20702" class="radio-link">
                            <div class="radio-name"><img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4gPHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4gPCEtLSBUYWxrIFJhZGlvIDcwMiAtLT4gPGRlZnM+IDxsaW5lYXJHcmFkaWVudCBpZD0icmFkaW83MDJHcmFkIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4gPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzM0NDk1RTtzdG9wLW9wYWNpdHk6MSIgLz4gPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojOTVBNUE2O3N0b3Atb3BhY2l0eToxIiAvPiA8L2xpbmVhckdyYWRpZW50PiA8L2RlZnM+IDxjaXJjbGUgY3g9IjMyIiBjeT0iMzIiIHI9IjMwIiBmaWxsPSJ1cmwoI3JhZGlvNzAyR3JhZCkiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+IDx0ZXh0IHg9IjMyIiB5PSIzOCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPjcwMjwvdGV4dD4gPCEtLSBSYWRpbyB3YXZlcyAtLT4gPHBhdGggZD0iTSA0NSAyMCBRIDUyIDMyIDQ1IDQ0IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiIG9wYWNpdHk9IjAuNyIvPiA8cGF0aCBkPSJNIDQ4IDI0IFEgNTQgMzIgNDggNDAiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBmaWxsPSJub25lIiBvcGFjaXR5PSIwLjUiLz4gPC9zdmc+" alt="Talk Radio 702" class="radio-icon"> Talk Radio 702</div>
                            <div class="radio-description">Johannesburg talk radio</div>
                        </a>
                        <a href="https://www.radio-browser.info/search?page=1&order=clickcount&reverse=true&hidebroken=true&name=Sky%20Radio%20Hits" class="radio-link">
                            <div class="radio-name"><img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4gPHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4gPCEtLSBTa3kgUmFkaW8gSGl0cyAtIE9mZmljaWFsIGZhdmljb24gLS0+IDxjaXJjbGUgY3g9IjMyIiBjeT0iMzIiIHI9IjMwIiBmaWxsPSJ1cmwoI3JhZGlvc2t5R3JhZCkiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+IDxkZWZzPiA8bGluZWFyR3JhZGllbnQgaWQ9InJhZGlvc2t5R3JhZCIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+IDxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM5QjU5QjY7c3RvcC1vcGFjaXR5OjAuOCIgLz4gPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRTY3RTIyO3N0b3Atb3BhY2l0eTowLjgiIC8+IDwvbGluZWFyR3JhZGllbnQ+IDwvZGVmcz4gPGltYWdlIGhyZWY9ImRhdGE6aW1hZ2UvcG5nO2Jhc2U2NCxpVkJPUncwS0dnb0FBQUFOU1VoRVVnQUFBRUFBQUFCQUNBSUFBQUFsQythSkFBQVRRMGxFUVZSNDJ1MWFlWkNkVlpVLzU5NzdiVy90MS8xNjM1Y3NKS1FUSUF0Q0FCRUlNV0VaV1hSWVZaWnlMSEVCYThaeFpxaVpZblJLeTJYR2dySktNNk1paUtnb0VCY1EwSVRWQkdJSVpFK1Q3azY2MCttOTMvNis3ZDR6Zjl4T0o0VEdzRnBTeGZkWFYvWDc3bmQvOTJ5Lzh6c1hpUWpleXcrRDkvanpQb0QzQWJ6TlI3eFRDeEdCSXBLS2dJQUFHQ0pqd0JtKzJ3RHc3V2NocFVncW1IVzdVdEc3amVGdEFWQUVSRWUzT0RUdTlneVdDbVVwSmFXVDV2eldhR1hDZUM5WWdDQmZESHNHaTcvWU1QekFrOE9EbzU0ZnFJWHRzUnZYTmwyN3FyNDZaV2tIUS94YkFrQUVVaW5CR1FBOHUzM3FCNzhiZk9LRmlmR3NEd1NoSWtTVWlxb3J6S3N2cVAvS2pYTnRpd1VoR1FML0pnQklJbElnT0FMQWs5c21mL2pid2UyOWhmMURwV3crQUFUSDVNaUFJUkpBS1IvTzdZamVlL3ZpcGZPVCtpUHZoaEhlWEJZS1FtVUlCaHg2aDhwLzJESisveDhQYjN4eFVwVWxqNGhFVEJDQlVvQUlpTUFRcVJEc1AxVE9GQVB0WmtyUnpML2VRU1RpVGJtTklSZ1I3T3pQcjFzL2VQZWpoN0paUDVFd3dSRktVU2dKQVJTQjV5c1ZVakp1ZEM1SXJsaFkwZEVRSVFMK3JxWFVOK0ZDUktRVVBMbHQ4aHMvN2R2dzRvUlNZSmxNU3BxQlIwQUl5RG5hRmo5N2Nlcm1pNW91V0pvV0F2Vi9Remx0Z1hjV2lYZ2pCMDlBQU1nUXYzbC83M2NmUERoVkNLVWt6cGxTQkVkcVZoZ3F0eWhUVmRiSHpxMjc2dno2K2EyeFZOd1FBZ2tBQVo1NWVmTEJwMFlZZ3dWdDhaV0xVcDBORWY0T3hmUUpMS0JQemhDb0ZIM3pwMzEzL3ZMZzRGRFJpZ3JCR1JFaEltZFE5bFJRbG5NN1kydFdWSis5cExLN005N1pHSm1wY1l6aHZiOGZ1dXZCQS8xRFpRV1VUaGhMNWlRL3Zycnh3aFZwYmRXM0dSQW5zSUJVWkFnc2xPWGRqd3grKzJmOUk1TmVxdElLUXFWTHJPdXIwSmVWS2V0RFo5V3VYcEcrK0FQVk5aV1dma3RLWWd3Wnc4bGNjTi9qUTV1ZkhZdlUyVUZJWXhQK29YRi9jVmQ4R2dBQXZuc3VSQUNDWTlHVjl6MCtkUHYvOWhUTE1oWVJYcUMwemJ4QUNZR3RkZEUxcDFkLyticU8raW9iQVB5QU9BZUdTQXdFeDFEU1EwK1A5QTJYamFScENvWkFRTlRkR1YvWUhwdHhnWGN4QmtnQkluei80WUd2L25pLzZ5dGtxQlRwTTBNR25QRHNKWldmdjZMMWdxWHBtU0psR25pa1BCTUFGdDN3eDQ4YzJqZFFkQndlU0pLS2dxSzhZRm5WaDArdjFqWjhDL0U4N2ZJNERWMjhudWR3aG96Qjl4NCtlT2N2K3lmeXZtTnloZ0FJZ3FFWEtJT3gyNjVxdlc1VlkxZGpSQmMxUlRDekd3SVNISWxnUjI5aDcwQlJlZEtJaUxLdkdNS1NreXZPV0pUaURHZlMxNXZkL1V6SVNFVlNrWmlOWFFJQVNFbTdEeGJ2ZmV4dzM0RmlzdEx5QTRVSUJzZHNJVXdsalM5YzJYYnp4YzMxVlJZQUJKTEVxODlTU2hBY0o3UEJocTBUWGtCTU1BQUlBbVdiYk5XSzZwUGJZa1F3YSt4cVRuNXNOWno1bFE1M1JCalArS0ZTVVp2SEl3Wm5LR1lsQ3diSG9pdS84NHYrWFgwRkt5TDBhU0ZDdGhpbVUrWU5hNXYrNmVwMjIrVGE0dzJPc3h3QmgvN2g4bStlR2ZGOGFWaGNBU2lwRU5sWjNSVTFLWk9BRUpIbzZMYW1Bd0tCSTNJMnk1SHJQdzRPdXovNDdVRFpsOG1ZV05BV245c2NGYTg5QTRhZ0ZHM2VtWGxndzNCbXlrOVdtSDZvQUlBSWsxSGo1a3VhLytPR0xvTXhJakRFN0RrUWtZaHc3MEJ4OC9ZTXQzbkU0a0dnRElQUGJZa3Q2b2d6aGw2Z0xBTUJqcmNERVFSU1NVbUlLRGdLamtkM3p4QUFOdTJhK3E5N2VnTTNCTTZxSzgwRmJiSGpBUVJTbVlKdDJaUDdsKy8xbEZ4cE9seFhVQ0EwQlA3enRSMjNYTlpxOGhNMG9rS3dvVEYzNjk0c0NJYUluR0d4RURZM09EZGUxRlNUc3ZSSjZ4Snh4T2FnclRnNFduN29tWkZudDJjcWs4YnkrY20xSDZpcHJqQjFKV1dBSlZlT1pYeEFBQVRMWWxQNWNQT3U3UEVBQk1OUXFzMjdNcHQzVEZrT0U1d3hnS0tyRU9HaU0rdXUrR0Jkek9GaHFMaVlQWDlNSnltQ2wzdnpUMi9QMkJZbkFzWkFsVUxMWkI4OHBkSXltUjhvMDJBQThQdm54emR1blZqWlhibjJqR3I5ZXQ5dytiSG54eDk3WVNJVzRVODhQN0ZwUitiYUN4dFhkcWNBa0FnT2pwUzM5ZVFzZ3lFS0lWak1aTW1vT0I0QVk5ZzdXUHJ6dml6ajB5eEFFakVPYzV0ak4xL1MxRnhqZTRFeXhBbUtKeUpzM1p2YnVUZkxEYVlVZVNGRjRzWkpyYkhtR2h1SVRJTk5aUDBITmd6L2JNUHd4aGNuZWdaTFhVM092SllZQVBRUHUzMURaU0xJRitYa2FMN3N5Y1Z6RWl1N1V3Z0FDSWNudkQvdHlPZ01XU3JMMnBSNTJyd0VPejYvQXV6c0srenFLeGdtUTBDRzRMcXlObVZkdmFwaDVhSkt5MkFNa2IzTy9na0FFUkNnNU1sOUE4VkN4bWNJbkdHcEZMYTN4ejV5ZGwwaUloakQ4YXkvYnYzQXY2N3JlV3JiSkdPNHZUZi91eitONnhYR00vNUVQalFOTkExbVJFVnpqWjFPbWpQckQ0NTV2VU5sQUJBY3laZXB1RmcrUHpsTEZocWU4ZytOZXd5QkNCaERWWloxbGRabFo5WFlKdE12L3dXNnFvUHV4WDI1b1RFWGJLNVRCN2xxWG5QMG5NVXBBUEFEOWZXZjlIMzN3UU9JYUprc2xGUjBaYUVjNmhYS3JpeTdFZ2dJS1BCa09tVzIxVG5UMkxMKzFuM1pjakcwWTRJekJGZldwS3h6VDYyYUpSeExaVmtzUzBRQUJFUUFTWTdGMm1vZE90S1V2TDQ4TVcySFAyNmQzRDFRTW0xT1JFVEFIVDYvSmRwVVl3UEFsNyszZDkzNkFjOVhDR0FaM1BkVUttNTBOVTJUdi83RHBjSzRLemhEUlBCVWE2MXpjbWRjazhMTk96TmJkbWU1eVJDQUlZQ3JrakdqdXlzK0N3RGJaSTdKanRaSkJDSUlRb1U0TFVPY29GZ3ErTk9PelBCUXliYVlJcEpFRlVsajZmeWs0UGlOKzNwLzlNaWhiQzVJeFkxUXFxa3hONTAwcnpxdi9vT25WQUpBcmhpT1pRTVpLRTBTMEdTdHRZNWpNaDJaeiszSWJPL0oyemJYcFpNbmpLYTBaUWcyQzRENktyTStiWVloQUlGVUlCd3hPT3IrNk5HaElDVEJVYXJYaGFBWE96emhEWTY1MHBPQ281UVErdXBEcDFiTmFZcHVmSEh5NnovcHk1VmtQQzdHczRGVXNIUko2dGFyMnE1YjNWQmZaU3NGMjNweWt6a2ZJMEpLVW9wcTY1ekdhbHNSS1lKOEtkeHpzSmlkOGdVSEFIQUQxZGdlWGRnZVZUUWJGNXJURWp1NUkvN25QVGxtTWluSmlZa0R3NlU3N242bHZkNVp2YUxhRU96MTVDM0dNQWhwMDY2cHNpZkJZa1NnQ01LUXp1NU9EWTY2MzdxL3IrUkpJRkFLS21MR0dZc3Fidjk0NStrTEs2WjdKcUxOdXpJRFl5NWFUSjlSZDN1OElXMHp4RkRSbzV2RzloOHFNWlBwc3dzOHRiQWx1cWdyd2ZBWUFOcTVRMG56VzZLcmxxWi85ZVJJS0JVZ0tFV214Zk9GOExZNzkwemxnK3RYTndEZ3NXWG9DTFVDeGlCYkRKNThjVEtUOTduQlEwbU1BVERjZTdENHd1N3NoaTNqbHNNVlVYM2ErdFRGelo5WTAxaVZORFhwNGh3VlFkOXdPVk9RbG1CU0VRSXNhSTgyVkprQUVBYnE3a2VHZHZZVm5LaVFFaEFBQXRYZUdKbmJIQ1Y2amJqTEVEbkRENTllL2FWck93SUp4V0pvR2N6Z2pIUHNPMXo2OTNYN2JyMXJ6KzREZWNaUUtncVBZWlRhc2Z5UTlnMlVTaTdwQ3NBWVdpWmIvK3pvNDFzbXBDVFhWNmVmbEx6anhxNmJMbTVLVjVnNnFLUUNBQ2g3YXV2ZWZIN0tjeXptQitUNWFrRmJ0S25HTHJueXVSMVRMKzNQaDY0VUFvaUlBQXliejJ1SnhSMmhYc3RHR1FPbElKVXdQblZKUzlsVDMzOTRZR3pNZFdLQ2M0d1pvdjlnOGE0SERtUUx3UmV1YU92dVNtaUw2Y1NxRFRpUjlYc0dTNTZ2YkpzcFJRakFHQXlNdW94aEpDWmE2eUtmdjdMdDhuUHJ1T2JrQWhGQjE5S2hjWGQ0d3BXQkFrTE9zRHBsZERSR0hZc2ZHblhYL1hvd1d3d01teWtGa29BaE5EVTRyYldPem5oczFqcXFGS1dUeGxkdW12TzVLMXZiV3FLQVVIYWxINmlxV29jSTd2bjk0YS9kMTdldEo2Y1VhTjVQQkp3akVmUU5sUTZOdTFJcWZwUUdReUlxUUtsazFMajJ3c1pMejY1RlJOZFh1aVlxQW9ZWWhHcFhmNTRRME9KbFgwWXN0bngrc3FYR2xvcWUzNXQ3Wk5ONDJWT0d3WWxBOCtKVDV5YWFxbTI5MWRrQmFQOVdCUDkyZmVkL2YvYWs3czY0YVRDcHFPeEoyK1FJOE11Tkk3ZXY2OW04TzZPZGg0Z1lZcjRVN2g4cWN3YkFnSTdUSVgwVmkvRHV6aGhqeUJETUl4MGNLUUNBYkNIY3VpOVhjaVV6MEErVlpiTHVya1JqMnU0WkxQLzQwVU1sVCtLUi9rdkg5NHFUa2gwTmppYXpmNGxYNmloZCs0SHE3OTYyNE1wejZ3Q2c3RW5UUk01UUVUMjJaZnlyOS9SdTJEcXBtM2NBR0pyd1huNGxCd1NjTVcwV1JjUVFTSUd3K0hqR2YraXBFZDlYQUtENStVemtGTXJoM2dORnoxZW1ZRElnMjJRbnQ4Y2pObi80bVpGSC8zRFlOcG5CVVJFaEFpa0twVnJTbGFpSUdhRWtoaWVhMEdoUjl0UzV5UzlkM2ZISk5ZMFJpMDlOZXFiSmJJTVJ3ZVBQalA3ZmJ3ZEhwenhGQUFCalUvNytReVVBNEJ4OVJSR2IxMVpZa2pDUXlyWjVyaGorNXJuUjc2OGZ5QlFDMitUQkVRdzZneFZkcVIwU1hGbVpNTmFjbnY3Vnh1RWZyQjl3RlJWS1V2ZXJVcEVRMkZKak42WXQ3ZWNuSGpFWkFvT1FRa2tMMm1OZi9GajdKOVkwVmxkYUpWZUdraElSNGZ0eTA0NnBUVHN6bnE4QVlDSVh2SExZSlFCVFlGQU1HNnV0NnovY2VOYmlsR2xnNkN2VFlKTzU0RHNQSFBqNUg0ZHp4ZEFRVENuU3lCbkRxTU1GUjZtQUNmUkQycndyZStlREIvZnR5bGJWT25PYUk0WkFSZUFIS2g0VjU1MVdXWmswWitybWlXZGtoa0RPVUNxYTB4ejlsK3M2cjFuZHFDVUhQMUFzSXNxZWVtNzdsT3RKQUpqTStZZEh5bHFNSVZlMjFOcWZ1YnpsaXg5dDdXcU11S1hRRUdnSUhCd3RmK2ZuQjM2eGNjUVBGV1BJT1FKQTFPYnQ5UTRBbGNxaGxUQ0d4dDFQZjJ2bm4zZG43UnJydExueDg1ZFZPU1lMSllXK2lqbGkxZkxxVk55WTZlYmUwSkJQQzVwU1VrUGF2dWpNMnZtdE1ZWVFLRElGNWtwQjcxQXBrQVFBbVh3SXV0WVNRVlEwcGUyNmxIWCtzdlNxNWRVVmxaYVVRQVNPeFhmMTUrOThvUCtCamNPNmYxSUtxaExHT1VzcW93NkhVRGtHSndXSEo3ejhTUG55YzJvLy9YZk5oV0lZNkdRZFV0VG1TK1ltTElNUkFYdmpBR1lhUDBWUUdSUFZGUWJxUGhVQUVYWFRxSWlHSmwzZ2lBaEJTUFUxZG50akZBQTR3ODllM25yZDZzWmlNZVFNT1VmTFpOdDc4MSs3cC9mYlArc2J5L2lNQWVlNGNuSGxEV3ViT2x0aWsyTnVmc3hOeFkwdjNqam5QMithMDlVWTNkWlRjSDFGQU1rS2M5bjhSRXVObzVtTHJqemlqUXN5T2xkTzVZS3hUS0FWODhCVEZaWFd3bzU0MU9HWmZEaWU5VUV3QVBETGN1bXk5SG1uVmVtM0d0TFdaejdTTXBrUDduOWlTUHFxSW1rYVV1M3FMNjViUC9EeS9zSk5hNXRXTGs0bG8rTG1pNXU3dXhKN0R4YVZvdllHNS94bDFmVXBjLzJ6by9zR2kwcVJrdFRaSHJ0d1JiVnVSd25mekh4QUp3SExZUGxTK09STFV3ZEhkS1N5VWphb1QxdXJWNlJ0ayszdUwyUUxvYmFvRE9ScDh4Skw1eVdVQXExQnpHdUozbkZEVjZrY2J0cVpQVHpoZ2lMZ2JNLysvSjc5aFNWZDhaV0xVNkdrbGxxbnBkWTU5cnVEWSs3VEwwMzZvVElGK2tVNXZ6bDY1cUtVYnBKbU5QbzM1RUxzQ00rNzk3R2hleDg3NUlVU0VhUWs1dkNsODVMTFQ2b0FnSkVwcjFBS2RXQlZwTzA1VGRFakFpT1lnaEZCUjBQa3Jsc1hmdTdLMWdWdHNVaEV4QjBlUzVxWG5WZW5DU2xucU5tclVxUWxOd0RZc1QvMzdNdFRCa2RFdEJQR2FmT1NiWFVPNHJUM1RsdEFFOVRqU2RtMHo0QWlzZ3ltaStVM2Z0cDczeE5EZzZPZWFUQ0drTThGWjV4U2VjVzV0VWRaSUNLRmlsbjhvak9yRjNmR1o1RFBOSEVOYWV1V3kxcXYrbEI5NzFEcDRKZ2JqNHJUNWlUcTA5YXJaNWdJMHhNSkdCenpkdllYa0dFZ2FkV3lxcFdMSzJhUmNQU2JlQnlyUGlZRDVVdmhyNThiZTNUVDJPTmJKb1luM0pnamRJY3h2ejM2RDVjMno5aTBVQTdMZ1dJQUpUYzg5NVNxenNhSVVxL1MvdlhQWWc2UE9VNXJ2ZU1GU2gvTnF6NEdRS2lWTlJnY2M3ZnN5ZWJ5b2Uzd3NCQXVYMUJ4eXB5RWxpU08zYVBRQkNNTWlURWtvcUlyWFY4Rm9jb1Z3K0ZKZnp6anZmUksvbmVieDE3ZW0rTW1UOFdOa2lzOVQ4MXRqZDc2OTIwWG4xRVRzZmhNMDMxd3BLd2tOZFU1aXpwaXRzbUNrSTVWYmJUcHBTS2xpSFBVdTljOXc3RXloMUxBMlhRUHVXbDNWbXNMVldsclVVYzg1b2p3TlpLd2VPanBZZGRYZmtDNk5BNVBlcGxDVUhUbHdFajVwZjJGbmdNRkNNbU9pVVRDQ0VJcXV0SVAxTnkyNkcxWHRsMS9ZWk50SFZXcDZpcXQ2Z3JUQytuamE1bzZHNkw2dlBFMTlVUndCRDd0N2ppN3hrRUFHRXJhc0hXeS8zQVpCWm9DTHordmZrbFhZdFpXVnR6eVAzdGNUd1doUkp4MlB1MzlSS1FJYkZ2b29pMGxNQVJmd2ZJRkZaKzdvdldqNTlZWmdrbEY1aEUzdUdCNXV1akt2c1BsbXk5dXJrd1lSSDlKZ0hrdHRwbXBnbzdtYmEva250K1Z5VTE1VHR6b2FJaDhjazFqZTcxRE1NdUFVRnh6ZnYwUEh6bVUyNVdGT2djNEFrZkdrVFBVb3pzQ1VFUnVOb1JRTGVxdXZPYUMrdFVycXVjMFIzUm5mS3pwSFpOZnVyTFc5WlcrSC9IV0JsOVNBbklvbE1NblhoaWZ5UHZrcThxRWNkMkY5WXM3RThmSnFVY0IvT1BWN1NkM3hKNTZZZUpReHRzelVISmRtUy9Mb2hzeWhoWmpkU2tqWFdFMTF6aW56bzB2bVpNOGUwa3FHUlV6RTVCamQwa0VFWnRIYks3bDBiYzRPVUtkRCtURHo0eU9EcnVKbExsNlJmVlY1emM0Rm5zOVNXcDZTamxSQ0xidXpyN1lreXVWNVZRaHlCWkR3VEZtOGFaYXV5RnRkM2NtVHU2SXpSQnNIV1N6em5WMGE0WnY4ZG9PQUZLaEpPOTliT2d6Mzl5Smdicm1rcVpiTG10ZHNhQmltZ2ZNOXRIcHNkY0paMVZhS2NCMzlKYkFjWTl1cnpmdnpIemh6dDE3RGhaUFgxaHh4eWU3bGkybzBMTEY2MHI1K01iTS9kZTRlNFVBQUk3TnoxeVV1dlNzMnN2UHFlMXNpT2oyNk1TRGJ0S2w3eldpRzA0di9TNGUvSEdWcnVqSzhZd2ZjL2kwYW5TaU8xLzROM3Z4VlNyU2M3Ni8wcVcvZC9MeW9DSkFZT3dOV1IzZnYzcjhQb0QzQWJ5M24vOEhKeFpvWmNEaXBJNEFBQUFBU1VWT1JLNUNZSUk9IiB4PSIxMiIgeT0iMTIiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgLz4gPCEtLSBSYWRpbyB3YXZlcyAtLT4gPHBhdGggZD0iTSA0NSAyMCBRIDUyIDMyIDQ1IDQ0IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgZmlsbD0ibm9uZSIgb3BhY2l0eT0iMC42Ii8+IDwvc3ZnPg==" alt="Sky Radio Hits" class="radio-icon"> Sky Radio Hits</div>
                            <div class="radio-description">International hit music</div>
                        </a>
                        <a href="https://www.radio-browser.info/search?page=1&order=clickcount&reverse=true&hidebroken=true&name=Qmusic%20Non-Stop" class="radio-link">
                            <div class="radio-name"><img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4gPHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4gPCEtLSBRbXVzaWMgTm9uLVN0b3AgLSBPZmZpY2lhbCBmYXZpY29uIC0tPiA8Y2lyY2xlIGN4PSIzMiIgY3k9IjMyIiByPSIzMCIgZmlsbD0idXJsKCNyYWRpb3FtdXNpY0dyYWQpIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIvPiA8ZGVmcz4gPGxpbmVhckdyYWRpZW50IGlkPSJyYWRpb3FtdXNpY0dyYWQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPiA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRTkxRTYzO3N0b3Atb3BhY2l0eTowLjgiIC8+IDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6I0ZGNTcyMjtzdG9wLW9wYWNpdHk6MC44IiAvPiA8L2xpbmVhckdyYWRpZW50PiA8L2RlZnM+IDxpbWFnZSBocmVmPSJkYXRhOmltYWdlL3BuZztiYXNlNjQsaVZCT1J3MEtHZ29BQUFBTlNVaEVVZ0FBQUVBQUFBQkFDQUlBQUFBbEMrYUpBQUFTNzBsRVFWUjQycjFhV1hOY3gzWCtUbmZmZTJjR2c4Rk9nQVFJRWx6QmZaZEUyalFwYTZjc2hYSlpkbHh4cXVMS1kvNURJcjg3TDZuS2k1TktsZVBZc1pOSWppUEpsclZRbEVSU0VyaUtHNGlGNEFZU083SE5ET2JlMjkwbkQvZk9EQUNDSkdoSjdrS2h1TnlaMjZmUDZlOTg1enVIbUJsZjY0cStmL2J2K3kwaUVBQUMwZUsvbnI0V0E1ampId0JDUE5LR3dBeHJZM3NFQWZSbk5DRGFOQUVrNXZ4ekVDQ2Y1VnlXODNrdTVMbmdJd3hnRFVDUWtod1hxU1FsMDFSUlFaVVpTcWJtZW84ZjdCUDZ1a0pJYXc0RG5wcTBJOE5tb0o4SGI5dWhBVHM2d2hQak5wOUhXSUF4SUlLUTVDVW9reEcxOVdMSlVyRzhWYmEyaWNabGxLbWhoQWNoSHZvZTlaVWRmQlF0QUFBemVNZDBkK29yRjIxdmw3bDl5NDZQWW1ZR1dyTTFzTGI4ZkNuMGhZQVFKQ1c4aEtpdEU2MXRhdE4yWitkamF0MEdlSW1pWXhmMnc1ZnpnTFZnQ3lHanIrYkpTZDE5V1YvNlFuZGR0djAzN09nd3BpWjRKczg2QkJPRUlDbEFZdjVXbU1HV3JZV3hZRXRLSVpVV05iVmkrUXExZVllemQ3L2F0STFLWnR6amt6L1ZnT2hUeFgzWWtTSFQyNlV2bk5NWHp1cWVUanMwZ0RBZ3g0SGpRa3FRQUVVYkJjRDNoU0FRQ0xBTWE3Z3dBMnVwb2RIWnV0UDk1cFBPbm0rSUZXM3hlK2Y2NGN0NWdKbXpXZFBYRTU0NEdwNzRVRi90aHUvRGNVQUNJSUFmc3VrSDRTa0JCTFlJQXJHa3lYM3lPZmZ3OTlXYWRrajVwVDBRd1p5VVlOWTluY0dSZDhJVFIyMy9EYzdsWWN6Q3VGazYzZWozZkpNbzlzL3M2elRiejhaUVpVYnQySlA0NGQrb1BmdUlvOHZHRWNJK3lpVm1DOHVRRWxLYW9RRjk3TVBnMklmNjhua2VHMllka25LaEZJaG0zYm5JRW9ZeDBDSHJFRVlEeFN0TGdxUHZOQWFXSVFRNURod0hVb0lCdG5IRUN3SEFUb3lIbng4RGN5TFV6cjREUUduL2l6ZkFXZ2dCQ2ZZTHB2Tmk4TkY3d1NkSFRHODN3U0paUWE0WGU2YTBkYllJQ3F4RElvRkVncXByUkdXR0tpdEZSWVpTS1hnSmtvb0I2SUR6TTV5YjVxbEpPem5PRXhPY3paS1NjTno0TEl5QmxKUk1JdFRoaVkraEhNcFVxODNiUUJSdGFkRUdDQUdBcHliRHo0LzV2L3ROZUtZRFlSaERkUlE1cFdVTW1DRUluaWVxYTBSMXJXaGVMbHJieFBJVnNybEYxRGFJZEFiSkJJUUNHRnB6UG1mSHgreWRmdDNYWTdzN3piV3Jkdkl1Z3FDTXkxRmlWZ3BoRUo3OGxDb3pxZm9Hc2JRNWlzTkYzQUhtQ0N2dFFMLy85bStEZC83UDNMb095OEJjVUN1Qm85WWdvcm9HMWI3SjJiWkx0VzhXTGEyb3FpSFhJeVZMbUR2WHZRYkdjQkR3MkxDK2RDSDQ2TDN3OUdjOE1SNkhVR1FBQUNFNGx4UExtbE0vL2p2MytaY3BVd1ZtOWZBTUpRUkltc3ZuL2JkZUR6NTYzOTY1QlJKd3ZSaGtTcmZXV003bnlQTmsyeHBueDJOeTYwNjVhbzFzV2tiVnRRL25Ra0pDU0hKY3FrZzdEVXZsMm5hMWFidi8zcHVtOHlLTWdldkI2T2lNeUZGOGR6UjQ3eTI1YXEzYXN4ZHNIMmFBRUxCV256L3J2L0dyNE9QMzdPUUV1UW5JVXRnUUJDRU1PUXdwbFpKcjI5V21yYzdPSjlTT1BUS0M3ZGxCZFYreXllQVNqeUpLSnVXYTlhSnhHVlhYK0svL2grNjh5S0ZQVXNYM3dmVmdqTzY4RUo3NlZMWnZwc3IwQXd6Z0tMNzF4Yk16di9oWitOa3hCQVZLcG1CdE9lalpRak9JUlAwU3VYR3orKzNublgwSFpPT3lZdUFXZWRnOTREMFB5dWN3VG1ZWVRaV1Yzbk12UVJMLzh0LzA1UXRRVGhsZXJlV1pRbmkyUXozMkRXZlg0K3FCc0NQRHN5Y0x2L3lYOE5Sbm1NbEYxcytKZUdaWUs5dld1TTkreHozNG5GaStnbHgzOXFYL1V4WVJsQUlBMS9XKy9ZSWRHdVNKY1RzeUJPWW8rVUFJQ0ppZVR0MTFRVzNab2U1TEU0VFVaenI4Ly81RjJIRUMrVHpjSXE0QmtBbzY1REFVMVRYTzNtKzVUeDlTMjNhSnVvYXlXeDZ4S0ZuQUo5YUNDSW1rZStBWmU2UFBmL3UzY1JCR3Y0V3dvOFAyYXErOTA2OFd4bnRBOTNiNS8vdWI4TmlIQ0FLNEhnUVZDYkRnd0Nkclpjc0s1OERUM2d1SDFhYXQ4UWVqREUzaUsyQzRrWWVObHExdGF2ZmU0UE5qUERvU1d4V3RNTFNEZDB6WEpYV3Y4UURNNElEL3hxK0M0MGR0SVU5ZUlrNlcwWWVOQVVHdVd1c2Vlc1Y3K1h1aWZrbGNtaFN6NWxlem9uY1JRUXJadHM1WnZ6R1lQSUZDQVo1WENoQTdQcWE3TG92NXh3K3lFM2ZERDk0T2p2N1JqZzZUNjVialhvZ0lLMVQ3bHNTUC9qYng2bzlFL1pJaUNINTFXNTkvbkNRYkcxWDdabElPNnpCK0VUT1V3MU5UK2xxM21CUDNBQnV0VDMvdXYvazZEdytSVXVWNGtKTERBTXhxODdiRUQzL3NQbldJS2pQbE5QazFMU0lBVkprUnJXMlVUSldCaUVGSzhVemVEdDVSOC9pQzZid1F2UHVXdWRvTklTRmxmUHdrT0F3QnlIWHRpZS85eURuNERLVXFvRFhrMTNmMnM5RGNkVVg5RXFUVGNRaVV3aUh3TVRFaDRvZWlOVDBkZnZCT2VQSkVqTnhsbHNFd1dxMWE2eDMrUytmSjV5bFZBV05pN3ZsMUwyYVFvSFNHa2hVUXFyZ2xoaEJzRE9kekFnQ01qVGhNMEhFODdEaHV4MGJLTUY4Qys2VXQ3ck12ZVM4Y3BsUXFpaWo4R1ZZSnVCTUo4anlTb2x5UkVjRWFEbndCampITERnOEZIL3plWE8rRjQ4dy9BeS9oUHZtYys4SmhTbGNXa2Y3UHRrcE9GZ3V6QmJBRkVRZStQbjg2dkhER1pyUGtKZUtyS1NXQ0FGSTYyL2U0ejN4SE5pK0gwUUEvc2xBVjhka29VY3lydVJhNWpJRUo1d01HRWFSVUFJT0U3YjhSSFArUXgrK1d2UmFWdk5iSXBxWGVpNi9JOVJzaWN2RlFxV3hoUko5SGVCN2hBZ0FBL0FJSFBqTlRWTWNVaVNaNXJvaUEwblJlRE0rZGd1K1Q0OFJQQ0lFZ0VMWDF6dVA3bmQxN0taRzhWeEY0ZU9sOFA1QXRlZVBoOWd0WWE2Y21PWitEMFRHc0U4RVljaHlxckZJQTdQQmdlT0VjRDl5T0M1K1NOR20wWEwzV2Zlb1ExZFhQRmxFV1VYK2FzbGlVeTltUlFUdCtGLzRNcENNcUs4V1NKcXF0TDhlR2tQZDFEZ01FTGhUc3lERG5zbVdIQUd5dDhEeXFxVk1nMG4wOStzckZtTW1VT2EyaDZocTFkYWZhdEMyT3E4VkFma3kyWkhRdXB2ZUs3dW8wL2RkNWZBeUZBcVJEbFJtNWRKbFl2VjYxYjVLdGJUSHh2UDlKZ0FYbnBtMy9EZmcraU1wcWh0RklwbVRUTWdWamJGK3Z2WEVOamxNV0ZLeUZNWExkUm1mSFkxUlJzYUNpOUNEUUNBUFQzUmtjZlRjNGZ0UmM3K09aUE1VRkp6TXpoSlNOVGM3dXZlNXozNUZiOTRoMCtzRlhpTWZ2bW12ZHJFTnluTEtnRm9hVXpxaVZhNVFaNkRjM3J0clJFVXBYbEVPV0dZNmp0dXhVRzdiT3ZZdUxVQzc4SURoK3hQL3RmK292em5EZ1EydVNvbmoxS2ZvYU96emtmL0FIM2R2bHZmeXE5K0ozaStoODd4a1JBTjEvVS9mMXhvbWZ5enVVTmZWeVhidXl2VjEyNERZSEJVSkZLVUZBQ0ZIZnFOWnZwTnE2ZUZzUE5jQmFFTEh2NjQ1ai9xOS9IcDd0NERBa3gxazRZUnZEK1p5NWZNRm5obExlb1ZkaXFsTjZzdmhubmh5M3ZWZnN3RzFZRzhkYjVBVFhFWTFOY3ZVNm9YczY3ZmdZcEppdGpFTXAxYlpHTkxjK0d1UVRtYjd1d3UvK0t6eDNDa1pUdWpLdW9XWURUdlJYSVNpUmd1dWFLNWY4Ti8vSFhEcVBVQy9Rd2hIQ1hPM1dsNzdnd0FmTmlnSnJSVldOYUZraEdwY0swOWZMMDFPa3l1SEZvU2JsaUxYcnkwWFdZb1JlSVRBOUhYNzZzVDU1QW1DNENlaXdMQmdhalNCQUdKWlIzR2dveGRiYXF6M0JrWGZzME1BY3JsWTh5dkRjS1hQbEVpbW5uS0NZWWJSb1dTbmExaUNSRk9iMkxjN25TTWxaOU1NaWtaQXJWbEZWWmxIUlgzeHIySFZSbnp2SjA5UGxYWmEvRTh5VzJjN1IxcTBseCtIQ1ROaHhUUGQyemtGaElGSWY5SmtPTzNRSFFvQkVpWnN4U0xadlVxdlhBbEI4ZDVSOWZ4YlJBd1JSS2lVYUdzbExQb3F3ektibmlybDJ0WWpGUlRSalJpcWwyamZMZFJ0NWNseWZPMlh1M0lvZEhvVzFEblgvVGQzVDZleDh2RnhqS01tNWJIRGtIZDE5YVZhTkdxTzVxSzV4dG13VGpVdGhyZUpjRmpvc1A4UU1JWkdzRUpXWkJYejZBTElRK0hid0RvK1BsVk5oUlB1RWRMYnY4UTcvUUczY3lsTVRmbTE5OE81YmRuUzRyRnd3SXdocy8wMDdQQ2d6VlFDZ0hJUmhlTzVrY1B5b0hSdWxSREwyaVJBb3pNRHoxS2J0cW4wTEhCZldDZzU4V0Z0Q3VaaC9leDRTeVRsczVNR1pDK0JzamljbmVHWm1UaDRGcUxMU1BmQ00rNjJuUk9OU3VYYUQrOHlMYXRNMmhIcFdoVTVFeEdOamRteTA5SjI2OTBydzlodTIvd2JzckEwUXNkR1VxWGEvZVZDMHJJd09WOER5WFB4Q25FckxvYjhvSUdJZGN1Q3pOYlBjYlVGQ3BLdEVYUU5rbkhHcHBvN3FsM0M1Y3h6VnZlQjhqbWR5TWNiZXZobTgrMlp3NG1NRWZya29KNExSSXAxUkc3YzZ1L1pTSmhPSEU2bFpaU0hIZWkrMFpoM09LU2tlTGw5TFNFbGxzNHRGdHRZY1NjM0d3QmpPWlRtWHBkbFhpK2R6VmYzNThmQ1RJNXpMeGtwSExFWkpMc3lJbGxiM3FVTmlXVXY1dFVnbUlXVTVhb2xnTmZJNXptY2ZpYmhUS2lVcTBuRGNPWXE4dFhaaXpOenM0K3hVM0JtNTJtMnVkczh2cHExQktrVVJwL0FMcHZPaXVYV0RFc21JaXNaUEJnRlZWcWs5KzV5OSsrRzRwYWdSVkZWRGpsdU9TQ0syek5scEhocmt3SDg0aGhaZFJNa2tOVFJTWlZVczVaWXU5MHhlbi9sTVh6b1BaanMrcGs5OUZoZDk4WDJMeWc0V3RVdEU3WktvSzg3V3dCaXdLU2tyTUJyTXp1Njk3cFBQaWZxRzZGT3hBWEpwQzZVcVdPdXlSNGs0bnpNOVhUeHhkMUVGVkx4ZElWYXNrczNMNDk1ckpBOUtDZVdFWjA0R1I5L1RWN3VEOS8rZ3o1N2s2ZWxTY2dBelFKUkt5ZGFWc3FFUkFLVXFSRU9UeUZUSFBuUWNzSVdVY3RVYTk0V1huUjI3aStBZ2lwRzdlaDFsTWdpRCtNQ1l5WEU0OE1NdlRwbmJOK084dHJpbDJqZko5WnNZUlEyOTVJZDhQanh4dFBDdi8rVC83dGRtNkE2cFlzNGhSRWJLeG1hMWFpM1M2VWpCZGZidVY0L3RnOUU4TWM1M3h6ZzdMWnFhdlZkKzZENitIMUxCempsUXBUWnVNejFYWXQwelNpTFNnVEdtNTBwNHVrT3QzVWlWbVhsZDRZWHpBTE5zYWxZN2Rzc1RIOW5CZnBnUVVzV0pMSkd3ZzNlQ3dkdHhrbkhkTXZ2d0MwaFZxQzA3Uk51YVVvTlFidHppSGY0QkpSTG14alVPUTFGWHIzWS80VDc5SWxYWHdOcDUycXVTR3phTE14MUlKdWRrZmpEbnN1RW5IOGpsSzcxblg0U1FEMHJKUlFPZ2xMTjVoL25XVTRXM1h1ZkpjYXBRYzU4Um9QbGRWTFpXMXRZNyt3Nkl4cVdsL3lMWGN4Ny9wbHExVHQrNnhuNUJORFhMNXVWeHM1N20xOWJ5SnovOVIzdDN4UFJjUVhZNkxydVlRUUpTOHRBZ0NqTmlhYk5zYWk3S3V2Zlh6UWxnVUdXR3Fxck50VjQ3TWtRbEFKa0xyR1dUd3BEU0dlZUovZDdMcjRyb2RFdThuWWdxMHJKcG1XeHVGWFgxRkJIcGhkNHVYL3ZKVCtDNXR2K0c2ZTJtcUpzU0laSVEwSWJIaHUzZE1WbFRKNWExeENTbkJETHpObFRpeVZYVm9xcWFKOGJ0MEdEY1IxdXdGaVVDV08zWTQ3MzYxM0xOT2lwVjY3TVRmTFNOZXlZYjVrNnJXQ3RiVnJoN0Q1Z0w1K3pBYlJnZHg2NjFTQ1E0bHd0UGZFVFd1dU5qYXZ0dTBiajB2bFZzOFdXVVNEcmZPR2o2ZXV5MVhqczI4c0JiNzhqV05yVjVHeWxudmw1V2FwakhRSHJmeVNmNTJqLzhQU2xIcE5LY25kYlhlem1mbzlJbFl4c3hNM1B6bXVuclJYYWFYSmVTS1FoUjdQZlByY2kwWnQvbnNSSGJkVkZmdVdEdjNPVHM5SDI2TlhIdEx6STFzcUZCMU5hVDY4N3ZqRVFlS00xTjNIL2d5WUlKWUgzNWZQNmZmNnJQZEVSYTNad2FpaTJFb0dSYUxHdFJHN2JJOWsyeXRZMGFHa1FxRWx3dHp4VHM1TGdkN0xmWHJ1cWVLK1o2Yjh6UzUvWEE3M0VhS1NWV3J2WmUvSzc3ekNGUjM0ajUxMmFSTTNOUndPa3crT2o5d3IvL1RKOC9qVVF5SHNsZ2pvbUtNUndHSkNSbHFxaW1UbFRYVUdXR1VpbkkyQURPVHZQVUJFOU4ySWtKem1jQlVEUnJNNXRaRU1IeTdGRGhNQ0FTb25XRnMrK2c5K3hMYXV0MjBLUEp4cW9jQU1weDloM2txUW5vVUhkM3dtaTRYdHdvWjBDcVNOWGc3TFM5TzJxaWl4NTN4RGdpYWlDQzQ1TGpVRVc2T0E1Vnlwb01IYkxXcEp6STV2ajhFa2tZYTY3MzhjZ0lUMDRraU5YbUhSQnk4YTVRczRHY2trbnYyWmVnSFA3TnowMWZEM3dmc3NpcjJjSUFJQ2hGamxNTVNwNDdNbE4wMnZ6cENSMWxDZklTMEJwUnA2amNjU05LVmZCTVBqaDJoQ3JTY25rYjFkUXRua2ZLMTE1N2JRN0V1cTVhc1ZJdWErR0pDVHM4aERDSWlWY0o2bWRQVlM3NE14dVVTSUFFd2hDdXA5YXNjM1k5UWN4MmJQUWVOc29RZ21kbTRDaG41eE5sTVdFUm1vaGFvTHhLcEp6SDkxT21XcTV0RDQ5OXFLOTJvVkFnMTRQcmdtUnhlSXdmTkRiR0RHdTVNSU13cElxMFdMUGUzYlBQMmJ0ZnRLd3czWjMrMjIrRUowL3dUSjVjRDBxVllnODY1Sms4L01LajFGSHpEQ2locitPcXJidEVVN05jdVRyb09HNjdMdHVoQWM1T2MrQkh0UVdKNHZqZTdDYUF0V3dOTEpNUVNDWGxraWJSMUN6WHRxdHR1OVQyUFhMNUNnQnkrUXFxcnFXNkJ2M1pKMmJ3TmdLZkhCZEVQRDBGSVVUVE1xcXVLV1l1K2hLVHU4VVJHd0JtZUVDZjd0Q25QemU5Vit6d0lPZXliUFI4ZlR3YWNvcEdKMTFQVk5lSTVoYTVmck96ZlpmYXNKVnFhdU9xSlNKelJHYWczMy9yOWVEOTM5ditHMUdEaThOUXJWcnJ2ZnBYM2w5OG43eGtOT2YwMVkwZWh5Rm5wK3pRb0wxNVRkL29zd08zN09nb1QwK3pQd00yZ0NUWHBYUWwxZFNJSlV0bGM2dHNiYVBtWnFxcUZZbmsvZlpocDZmTXlVK0RvMy9VblJkaHRHaGU3aDU4M24zeVdhcXRleFF0K2NFRzNEdXE2ZnQyZW9xelU1elBZU2JQUVJDL3lYRW9rYVJVaWxKcFNsZkdZdTFjMlhSV3ZCVXBzZStiVzlmdHdHMVlRM1VOY3ZsS3FxcCs1QmJhWWllMkdCRDBDSE1RSlNsaFFRSmJHbjI4ZDY2UXhGZHR3TDJEOU13UG4zRllUQUFzaUx5UHVQNGZkcG1sa2xxZmY5VUFBQUFBU1VWT1JLNUNZSUk9IiB4PSIxMiIgeT0iMTIiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgLz4gPCEtLSBSYWRpbyB3YXZlcyAtLT4gPHBhdGggZD0iTSA0NSAyMCBRIDUyIDMyIDQ1IDQ0IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgZmlsbD0ibm9uZSIgb3BhY2l0eT0iMC42Ii8+IDwvc3ZnPg==" alt="Qmusic Non-Stop" class="radio-icon"> Qmusic Non-Stop</div>
                            <div class="radio-description">Continuous hit music</div>
                        </a>
                    </div>
                </div>
                
                <div class="features">
                    <div class="feature-card">
                        <h3><span class="icon" data-fallback="HOME">&#x1F3E0;</span> HOME ASSISTANT</h3>
                        <p>Control your smart home devices and automations with modern interface support</p>
                    </div>
                    <div class="feature-card">
                        <h3><span class="icon" data-fallback="♫">&#x1F3B5;</span> YOUTUBE MUSIC</h3>
                        <p>Stream music with full YouTube compatibility - no more "outdated browser" errors!</p>
                    </div>
                    <div class="feature-card">
                        <h3><span class="icon" data-fallback="FIND">&#x1F50D;</span> GOOGLE SEARCH</h3>
                        <p>Search the web with full modern browser support and enhanced performance</p>
                    </div>
                    <div class="feature-card">
                        <h3><span class="icon" data-fallback="TUBE">&#x1F4FA;</span> YOUTUBE</h3>
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
                
                // Check if Unicode icons are displaying properly
                function checkIconSupport() {
                    var testIcon = document.createElement('span');
                    testIcon.innerHTML = '&#x1F4BB;';
                    testIcon.style.position = 'absolute';
                    testIcon.style.left = '-9999px';
                    testIcon.style.fontSize = '16px';
                    document.body.appendChild(testIcon);
                    
                    // Wait a moment for the icon to render
                    setTimeout(function() {
                        var iconWidth = testIcon.offsetWidth;
                        document.body.removeChild(testIcon);
                        
                        // Use a more lenient check - if width is very small or zero, use fallbacks
                        if (iconWidth < 8) {
                            console.log('Unicode icons not supported on this system, using text fallbacks');
                            // Replace icons with fallback text from data-fallback attribute
                            var iconElements = document.querySelectorAll('.icon');
                            
                            iconElements.forEach(function(element) {
                                var fallback = element.getAttribute('data-fallback');
                                if (fallback) {
                                    element.innerHTML = fallback;
                                    element.className += ' icon-fallback';
                                    element.style.fontWeight = 'bold';
                                    element.style.fontSize = '0.9em';
                                }
                            });
                        } else {
                            console.log('Unicode icons are supported');
                        }
                    }, 50);
                }
                
                // Run icon check after a short delay
                setTimeout(checkIconSupport, 100);
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
                # Hide keyboard - kill all instances to prevent conflicts
                logging.info("Hiding virtual keyboard (wvkbd)")
                subprocess.run(['pkill', '-f', 'wvkbd-mobintl'], check=False)
                # Give it a moment to fully terminate
                time.sleep(0.5)
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
                    # Wayland-optimized command with compact, movable keyboard
                    cmd = [
                        'wvkbd-mobintl',
                        '-L', '180',  # Shorter landscape height (was 300)
                        '--bg', '333333cc',  # Semi-transparent dark background
                        '--fg', 'ffffff',     # White text
                        '--layer', 'overlay',  # Use overlay layer to appear above fullscreen apps
                        '--anchor', 'bottom'   # Anchor to bottom to leave text area clear
                    ]
                    logging.info("Using compact Wayland keyboard (180px height, bottom-anchored)")
                else:
                    # X11 fallback with compact keyboard
                    cmd = [
                        'wvkbd-mobintl',
                        '-L', '160',  # Shorter landscape height for X11
                        '--fg', 'white'
                    ]
                    logging.info("Using compact X11 keyboard (160px height)")
                
                # Start keyboard process
                try:
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # Quick check if process started successfully
                    time.sleep(0.1)
                    if process.poll() is not None:
                        # Process died immediately, try without anchor if that was the issue
                        if '--anchor' in cmd:
                            logging.warning("Anchored keyboard failed, trying without anchor...")
                            cmd_no_anchor = [arg for arg in cmd if arg != '--anchor' and arg != 'bottom']
                            process = subprocess.Popen(cmd_no_anchor, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            time.sleep(0.1)
                        
                        # If still failing, try basic fallback
                        if process.poll() is not None:
                            logging.warning("Compact keyboard failed, trying basic wvkbd")
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
    
    def cleanup_keyboard_processes(self):
        """Clean up any leftover keyboard processes from previous sessions"""
        try:
            logging.info("Cleaning up any leftover virtual keyboard processes...")
            # Kill any existing wvkbd processes
            result = subprocess.run(['pkill', '-f', 'wvkbd-mobintl'], capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("Cleaned up existing wvkbd processes")
                time.sleep(0.5)  # Give processes time to terminate
            else:
                logging.info("No existing wvkbd processes found")
        except Exception as e:
            logging.warning(f"Could not clean up keyboard processes: {e}")
    
    def check_for_updates(self):
        """Check for updates and show status notification"""
        if not self.is_raspberry_pi:
            # Only check for updates on Raspberry Pi
            return
            
        try:
            # Check if update script exists
            update_script = os.path.join(os.path.dirname(__file__), "scripts", "update_check.sh")
            if not os.path.exists(update_script):
                logging.info("Update script not found, skipping update check")
                return
            
            # Check if we're in a git repository
            if not os.path.exists(".git"):
                logging.info("Not in a git repository, skipping update check")
                return
            
            logging.info("Checking for updates in background...")
            
            # Run update check in background (non-blocking)
            # The update_check.sh script will handle automatic updates based on configuration
            try:
                # Start the update check process in the background
                process = subprocess.Popen(
                    [update_script],
                    cwd=os.path.dirname(__file__),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Use a timer to check the process status after a short delay
                # This allows the UI to load without blocking
                from PyQt6.QtCore import QTimer
                self.update_timer = QTimer()
                self.update_timer.setSingleShot(True)
                self.update_timer.timeout.connect(lambda: self.check_update_status(process))
                self.update_timer.start(2000)  # Check after 2 seconds
                
            except Exception as e:
                logging.error(f"Error starting update check: {e}")
                
        except Exception as e:
            logging.error(f"Error in update check: {e}")
    
    def check_update_status(self, process):
        """Check the status of the update process"""
        try:
            # Check if process is still running
            if process.poll() is None:
                # Process still running, check again later
                self.update_timer.start(5000)  # Check again in 5 seconds
                return
                
            # Process completed, get the output
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                # Update check completed successfully
                output = stdout.strip()
                if "UPDATES_APPLIED_AUTOMATICALLY" in output or "Updates applied automatically" in output:
                    self.show_update_notification("Updates have been applied automatically! Application will restart with the new version.", True)
                elif "Updates are available" in output and "Applying updates automatically" not in output:
                    self.show_update_notification("Updates are available but auto-apply failed.", False)
                elif "Already up to date" in output:
                    logging.info("Application is already up to date")
                else:
                    logging.info(f"Update check completed: {output}")
                    # Check for restart flag file as backup detection
                    if os.path.exists("/tmp/kiosk-restart-needed"):
                        self.show_update_notification("Updates have been applied! Application will restart with the new version.", True)
                        # Clean up the flag file
                        try:
                            os.remove("/tmp/kiosk-restart-needed")
                        except OSError:
                            pass
            else:
                # Update check failed
                logging.warning(f"Update check failed with return code {process.returncode}")
                if stderr:
                    logging.warning(f"Update check error: {stderr}")
                    
        except Exception as e:
            logging.error(f"Error checking update status: {e}")
    
    def show_update_notification(self, message, is_critical=False):
        """Show update notification to user"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            
            if is_critical:
                # Critical update notification (auto-restart)
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Automatic Update Applied")
                msg_box.setText("Office Kiosk Browser has been updated automatically!")
                msg_box.setInformativeText(f"{message}\n\nThe application will restart automatically in a few seconds to apply the new version.")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.show()
                
                # Schedule application restart
                from PyQt6.QtCore import QTimer
                restart_timer = QTimer()
                restart_timer.setSingleShot(True)
                restart_timer.timeout.connect(self.restart_application)
                restart_timer.start(5000)  # Restart in 5 seconds to give user time to read
                
                # Auto-close the dialog after 4 seconds
                auto_close_timer = QTimer()
                auto_close_timer.setSingleShot(True)
                auto_close_timer.timeout.connect(msg_box.accept)
                auto_close_timer.start(4000)
                
            else:
                # Info notification
                QMessageBox.information(
                    self,
                    "Update Information",
                    f"{message}\n\nAutomatic updates are enabled. Updates will be applied automatically when the application starts."
                )
                
        except Exception as e:
            logging.error(f"Error showing update notification: {e}")
    
    def restart_application(self):
        """Restart the application after updates"""
        try:
            logging.info("Restarting application after automatic update...")
            
            # Close current instance
            self.close()
            
            # Restart using the start script
            start_script = os.path.join(os.path.dirname(__file__), "scripts", "start_kiosk.sh")
            if os.path.exists(start_script):
                subprocess.Popen([start_script], cwd=os.path.dirname(__file__))
            else:
                # Fallback to direct Python restart
                python_executable = sys.executable
                subprocess.Popen([python_executable, __file__])
                
        except Exception as e:
            logging.error(f"Error restarting application: {e}")
    
    # ...existing code...
def main():
    """Main function to run the application"""
    
    # Better single-instance check using process name matching
    current_pid = os.getpid()
    script_name = "kiosk_browser.py"
    
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['wmic', 'process', 'where', f'name="python.exe"', 'get', 'ProcessId,CommandLine'], 
                                  capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if script_name in line and 'ProcessId' not in line:
                    # Extract PID from the line
                    parts = line.strip().split()
                    if parts:
                        try:
                            pid = int(parts[-1])
                            if pid != current_pid:
                                print("Office Kiosk Browser is already running.")
                                print("Only one instance is allowed. Exiting.")
                                sys.exit(0)
                        except (ValueError, IndexError):
                            continue
        else:  # Unix/Linux
            result = subprocess.run(['pgrep', '-f', script_name], capture_output=True, text=True)
            if result.returncode == 0:
                pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip().isdigit()]
                other_pids = [pid for pid in pids if pid != current_pid]
                if other_pids:
                    print(f"Office Kiosk Browser is already running (PIDs: {other_pids}).")
                    print("Only one instance is allowed. Exiting.")
                    sys.exit(0)
    except Exception as e:
        logging.warning(f"Could not check for existing instances: {e}")
        # Continue anyway - single instance check is just a safety feature
    
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
    
    # Set application properties for better Qt6 WebEngine storage identification
    app.setApplicationName("OfficeKioskBrowser")
    app.setApplicationDisplayName("Office Kiosk Browser Qt6")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("OfficeKiosk")
    app.setOrganizationDomain("office-kiosk.local")
    
    # Set additional Qt properties for WebEngine storage
    if hasattr(app, 'setDesktopFileName'):
        app.setDesktopFileName("office-kiosk-browser")
    
    # Configure Qt6 WebEngine environment for better storage
    os.environ.setdefault('QT_LOGGING_RULES', '*.debug=false;qt.webenginecontext.debug=true')
    
    logging.info(f"Qt Application configured:")
    logging.info(f"  Name: {app.applicationName()}")
    logging.info(f"  Display Name: {app.applicationDisplayName()}")
    logging.info(f"  Version: {app.applicationVersion()}")
    logging.info(f"  Organization: {app.organizationName()}")
    logging.info(f"  Domain: {app.organizationDomain()}")
    
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
