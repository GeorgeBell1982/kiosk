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
import shutil
import tempfile
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFrame, QMessageBox, QLabel, QSizePolicy)

# Try to import WebEngine
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile, QWebEnginePage
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

from PyQt6.QtCore import QUrl, Qt, QSize, QTimer, QLockFile, QProcess
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QShortcut, QKeySequence

# Try to import SVG support for Qt6
try:
    from PyQt6.QtSvg import QSvgRenderer
    SVG_AVAILABLE = True
    logging.info("Qt6 SVG support available")
except ImportError:
    logging.warning("Qt6 SVG support not available - using fallback icons. Install python3-pyqt6.qtsvg or reinstall PyQt6 for SVG icon support.")
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
        self.keyboard_process = None
        self.keyboard_stopping = False
        self.keyboard_restore_fullscreen = False
        self.keyboard_error = ""
        self.closing = False
        self.radio_dialog = None
        self.playing_station = -1
        
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
        self.setup_shortcuts()
        self.check_for_updates()  # Check for updates on startup
        self.load_home_page()
        
    @staticmethod
    def detect_raspberry_pi():
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
            # Fit the current display rather than assuming a 1024x600 panel.
            available = self.screen().availableGeometry()
            self.setGeometry(available.x(), available.y(),
                             min(1024, available.width()), min(600, available.height()))
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
            # A named profile is required for cookies and storage to survive restarts.
            self.web_profile = QWebEngineProfile("office-kiosk", self.web_view)
            self.web_view.setPage(QWebEnginePage(self.web_profile, self.web_view))
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
        
    def setup_shortcuts(self):
        for sequence, callback in [('F11', self.toggle_fullscreen),
                                   ('F12', self.toggle_dev_tools),
                                   ('Ctrl+R', self.web_view.reload)]:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)

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
        # Reserve enough vertical space for two rows of touch targets.
        control_height = 160  # Two rows of touch targets plus frame padding
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
        control_layout.setSpacing(12)
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
        nav_height = control_height - 40
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
        
        # Layouts distribute the available width; keep touch targets usable at 800px.
        icon_size = QSize(24, 24)

        self.back_btn = QPushButton()
        self.back_btn.setIcon(self.load_icon('back'))
        self.back_btn.setIconSize(icon_size)
        self.back_btn.clicked.connect(self.web_view.back)
        self.back_btn.setMinimumWidth(44)
        self.back_btn.setFixedHeight(44)
        self.back_btn.setStyleSheet(nav_button_style)
        self.back_btn.setToolTip("Go Back")
        
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(self.load_icon('forward'))
        self.forward_btn.setIconSize(icon_size)
        self.forward_btn.clicked.connect(self.web_view.forward)
        self.forward_btn.setMinimumWidth(44)
        self.forward_btn.setFixedHeight(44)
        self.forward_btn.setStyleSheet(nav_button_style)
        self.forward_btn.setToolTip("Go Forward")
        
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(self.load_icon('refresh'))
        self.refresh_btn.setIconSize(icon_size)
        self.refresh_btn.clicked.connect(self.web_view.reload)
        self.refresh_btn.setMinimumWidth(44)
        self.refresh_btn.setFixedHeight(44)
        self.refresh_btn.setStyleSheet(nav_button_style)
        self.refresh_btn.setToolTip("Refresh Page")
        
        self.home_btn = QPushButton()
        self.home_btn.setIcon(self.load_icon('home'))
        self.home_btn.setIconSize(icon_size)
        self.home_btn.clicked.connect(self.load_home_page)
        self.home_btn.setMinimumWidth(44)
        self.home_btn.setFixedHeight(44)
        self.home_btn.setStyleSheet(nav_button_style)
        self.home_btn.setToolTip("Go Home")
        
        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.setIcon(self.load_icon('fullscreen'))
        self.fullscreen_btn.setIconSize(icon_size)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setMinimumWidth(44)
        self.fullscreen_btn.setFixedHeight(44)
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
            self.keyboard_btn.setMinimumWidth(44)
            self.keyboard_btn.setFixedHeight(44)
            self.keyboard_visible = False  # Track keyboard state
            self.update_keyboard_button_style()
            self.keyboard_btn.setToolTip("Toggle Virtual Keyboard")
            nav_bottom_row.addWidget(self.keyboard_btn)
            
            # Shutdown button
            self.shutdown_btn = QPushButton()
            self.shutdown_btn.setIcon(self.load_icon('shutdown'))
            self.shutdown_btn.setIconSize(icon_size)
            self.shutdown_btn.clicked.connect(self.shutdown_pi)
            self.shutdown_btn.setMinimumWidth(44)
            self.shutdown_btn.setFixedHeight(44)
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
        shortcuts_group.setFixedHeight(nav_height)
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
            ("RADIO", None, "#9b59b6", "radio"),
            ("GOOGLE", "https://www.google.com", "#27ae60", "google"),
            ("YOUTUBE", "https://www.youtube.com", "#c0392b", "youtube")
        ]
        
        shortcut_font_size = 10

        self.shortcut_buttons = []
        for i, (name, url, color, icon_name) in enumerate(shortcuts):
            btn = QPushButton(name)
            btn.setIcon(self.load_icon(icon_name))
            btn.setIconSize(QSize(18, 18))
            btn.setMinimumWidth(44)
            btn.setFixedHeight(44)
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
            if name == "RADIO":
                btn.clicked.connect(self.show_radio)
            else:
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
        control_layout.addWidget(nav_controls_group, 4)
        control_layout.addWidget(shortcuts_group, 3)

        for button in control_frame.findChildren(QPushButton):
            # Taps should not steal focus from a web form; Tab navigation still works.
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
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
        
        # Keep web isolation enabled; the embedded home page needs no local resource access.
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        
        # Load normal page resources without granting popup or clipboard access.
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, False)
        
        # Preserve media playback and local-network WebRTC for Home Assistant cameras.
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, False)
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
            self.web_view.loadFinished.connect(self.sync_radio_home)
        if hasattr(self.web_view, 'loadProgress'):
            self.web_view.loadProgress.connect(self.on_load_progress)
        
        logging.info("Qt6 WebEngine setup complete with modern compatibility")
        
    def show_radio(self):
        if not WEBENGINE_AVAILABLE:
            QMessageBox.warning(self, "Radio unavailable", "Radio requires PyQt6-WebEngine.")
            return
        if self.radio_dialog is None:
            from radio_player import RadioDialog
            self.radio_dialog = RadioDialog(self)
            self.radio_dialog.playbackChanged.connect(self.on_radio_playback)
        available = self.screen().availableGeometry()
        self.radio_dialog.resize(min(720, available.width()), min(520, available.height()))
        self.radio_dialog.show()
        self.radio_dialog.raise_()
        self.radio_dialog.activateWindow()

    def play_radio_station(self, index):
        self.show_radio()
        if self.radio_dialog is not None:
            self.radio_dialog.play_station(index)

    def on_radio_playback(self, station, playing):
        self.playing_station = station if playing else -1
        self.sync_radio_home()

    def sync_radio_home(self, success=True):
        if self.closing or not success:
            return
        from radio_player import HOME_URL
        if self.web_view.url().adjusted(QUrl.UrlFormattingOption.RemoveFragment) != QUrl(HOME_URL):
            return
        self.web_view.page().runJavaScript("""
            document.querySelectorAll('[data-station]').forEach(button => {
                const active = Number(button.dataset.station) === %d;
                button.classList.toggle('is-playing', active);
                button.setAttribute('aria-current', String(active));
                const name = button.querySelector('.station-name').textContent;
                button.setAttribute('aria-label', name + (active ? ' — Playing' : ''));
            });
        """ % self.playing_station)

    def load_home_page(self):
        """Show station buttons immediately, without a welcome banner or scrolling."""
        if not WEBENGINE_AVAILABLE:
            return
        from radio_player import HOME_URL, radio_home_html
        self.web_view.setHtml(radio_home_html(), QUrl(HOME_URL))

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
        from radio_player import HOME_URL, STATIONS
        home_url = url.adjusted(QUrl.UrlFormattingOption.RemoveFragment)
        if home_url == QUrl(HOME_URL):
            for index in range(len(STATIONS)):
                if url.fragment() == f"station/{index}":
                    # Fragment links keep the home page in place and avoid a network load.
                    self.web_view.page().runJavaScript("history.replaceState(null, '', '/')")
                    self.play_radio_station(index)
                    return
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
        # An explicit choice overrides the keyboard's automatic fullscreen restore.
        self.keyboard_restore_fullscreen = False
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def toggle_virtual_keyboard(self):
        """Start or stop only the keyboard process owned by this browser."""
        if not self.is_raspberry_pi:
            QMessageBox.warning(self, "Not Available", "Virtual keyboard is only available on Raspberry Pi.")
            return
        if self.closing:
            return
        if self.keyboard_process is not None:
            self.stop_virtual_keyboard()
            return
        if not (os.environ.get('WAYLAND_DISPLAY') or
                os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'):
            QMessageBox.information(self, "Wayland Required",
                                    "wvkbd requires a Wayland desktop and a compatible compositor. "
                                    "For an X11 desktop, use an X11 virtual keyboard such as Onboard.")
            return
        executable = shutil.which('wvkbd-mobintl')
        if executable is None:
            self.show_keyboard_install_dialog()
            return

        process = QProcess(self)
        self.keyboard_process = process
        self.keyboard_stopping = False
        self.keyboard_error = ""
        # These height options work in both older packaged wvkbd and current releases.
        # The keyboard already anchors itself at the bottom; do not invent layer flags.
        process.setProgram(executable)
        process.setArguments(['-H', '180', '-L', '180'])
        process.setStandardInputFile(QProcess.nullDevice())
        process.setStandardOutputFile(QProcess.nullDevice())
        process.readyReadStandardError.connect(lambda: self.read_keyboard_error(process))
        process.started.connect(lambda: self.keyboard_started(process))
        process.finished.connect(lambda code, status: self.keyboard_finished(process, code, status))
        process.errorOccurred.connect(lambda error: self.keyboard_process_error(process, error))
        process.start()

    def show_keyboard_install_dialog(self):
        QMessageBox.information(self, "Virtual Keyboard Not Installed",
                                "Install wvkbd with:\nsudo apt update\nsudo apt install wvkbd\n\n"
                                "Then use the keyboard button in a Wayland desktop session.")

    def keyboard_started(self, process):
        if process is not self.keyboard_process:
            return
        if self.closing or self.keyboard_stopping:
            process.kill()
            return
        if self.isFullScreen():
            self.keyboard_restore_fullscreen = True
            # Maximized windows respect the keyboard's compositor exclusive zone.
            self.showMaximized()
        self.keyboard_visible = True
        self.update_keyboard_button_style()
        self.web_view.setFocus(Qt.FocusReason.OtherFocusReason)

    def read_keyboard_error(self, process):
        # Drain stderr while the keyboard runs, retaining only a short diagnostic tail.
        output = bytes(process.readAllStandardError()).decode('utf-8', errors='replace')
        if process is self.keyboard_process:
            self.keyboard_error = (self.keyboard_error + output)[-2048:]

    def keyboard_process_error(self, process, error):
        if error == QProcess.ProcessError.FailedToStart and process is self.keyboard_process:
            self.keyboard_error = process.errorString()
            self.keyboard_finished(process, -1, QProcess.ExitStatus.CrashExit)

    def keyboard_finished(self, process, exit_code, exit_status):
        if process is not self.keyboard_process:
            return
        self.read_keyboard_error(process)
        stopped = self.keyboard_stopping or self.closing
        self.keyboard_process = None
        self.keyboard_visible = False
        self.keyboard_stopping = False
        self.update_keyboard_button_style()
        process.deleteLater()
        restore = self.keyboard_restore_fullscreen
        self.keyboard_restore_fullscreen = False
        if restore and not self.closing:
            self.showFullScreen()
        if not stopped and (exit_code != 0 or exit_status == QProcess.ExitStatus.CrashExit):
            logging.warning("Virtual keyboard failed: %s", self.keyboard_error)
            QMessageBox.warning(self, "Keyboard Failed to Start",
                                "The virtual keyboard stopped unexpectedly. Check that the Wayland "
                                "compositor supports wlr-layer-shell and virtual-keyboard protocols.\n\n"
                                + self.keyboard_error)

    def stop_virtual_keyboard(self, force=False):
        """Stop asynchronously, escalating to kill if the owned process ignores TERM."""
        process = self.keyboard_process
        if process is None or (self.keyboard_stopping and not force):
            return
        self.keyboard_stopping = True
        self.keyboard_visible = False
        self.update_keyboard_button_style()
        if force or process.state() == QProcess.ProcessState.Starting:
            process.kill()
        else:
            process.terminate()
            timer = QTimer(process)
            timer.setSingleShot(True)
            timer.timeout.connect(process.kill)
            timer.start(1000)

    def update_keyboard_button_style(self):
        """Update the keyboard button style based on current state"""
        if not hasattr(self, 'keyboard_btn'):
            return
        
        # Get the current font size from the nav buttons
        font_size = 14
        
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
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.keyboard_restore_fullscreen = False
            self.showNormal()
            event.accept()
            return
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Clean up when the application is closing"""
        self.closing = True
        if self.radio_dialog is not None:
            self.radio_dialog.shutdown()
        self.stop_virtual_keyboard(force=True)

        if hasattr(self, 'dev_tools'):
            self.dev_tools.close()
        # The updater retains its own output handle until it exits, even if we close.
        if getattr(self, 'update_output', None) is not None:
            self.update_output.close()
            self.update_output = None
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

        # Call parent closeEvent to ensure proper cleanup
        super().closeEvent(event)
        
    def toggle_dev_tools(self):
        """Toggle developer tools for debugging"""
        if not WEBENGINE_AVAILABLE:
            return
            
        try:
            page = self.web_view.page()
            if hasattr(page, 'setDevToolsPage'):
                if not hasattr(self, 'dev_tools'):
                    self.dev_tools = QWebEngineView(self)
                    self.dev_tools.setWindowFlag(Qt.WindowType.Window, True)
                    page.setDevToolsPage(self.dev_tools.page())
                if self.dev_tools.isVisible():
                    self.dev_tools.hide()
                else:
                    self.dev_tools.show()
                    self.dev_tools.raise_()
            else:
                logging.warning("Developer tools not available")
        except Exception as e:
            logging.error(f"Error opening developer tools: {e}")
    
    def check_for_updates(self):
        """Check for updates and show status notification"""
        if not self.is_raspberry_pi:
            # Only check for updates on Raspberry Pi
            return
            
        if getattr(self, 'update_process', None) is not None:
            return

        try:
            # Check if update script exists
            update_script = os.path.join(os.path.dirname(__file__), "scripts", "update_check.sh")
            if not os.path.exists(update_script):
                logging.info("Update script not found, skipping update check")
                return
            
            # Check if we're in a git repository
            if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".git")):
                logging.info("Not in a git repository, skipping update check")
                return
            
            logging.info("Checking for updates in background...")
            
            # Run update check in background (non-blocking)
            # The update_check.sh script will handle automatic updates based on configuration
            try:
                # Start the update check process in the background
                # A child can fill a pipe before polling sees it exit. A temporary
                # file drains output without blocking the child or the GUI thread.
                self.update_output = tempfile.TemporaryFile()
                try:
                    process = subprocess.Popen(
                        ['bash', update_script],
                        cwd=os.path.dirname(__file__),
                        stdin=subprocess.DEVNULL,
                        stdout=self.update_output,
                        stderr=subprocess.STDOUT,
                    )
                except Exception:
                    self.update_output.close()
                    self.update_output = None
                    raise
                self.update_process = process
                
                # Use a timer to check the process status after a short delay
                # This allows the UI to load without blocking
                from PyQt6.QtCore import QTimer
                self.update_timer = QTimer(self)
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
                
            # Read the end of the log, where the script emits its result marker.
            # Bound memory use even when dependency installation is very verbose.
            self.update_output.seek(0, os.SEEK_END)
            self.update_output.seek(max(0, self.update_output.tell() - 65536))
            stdout = self.update_output.read().decode('utf-8', errors='replace')
            self.update_output.close()
            self.update_output = None
            self.update_process = None
            
            if process.returncode == 0:
                # Update check completed successfully
                output = stdout.strip()
                if "UPDATES_APPLIED_AUTOMATICALLY" in output or "Updates applied automatically" in output:
                    self.show_update_notification("Updates have been applied automatically! Application will restart with the new version.", True)
                elif "automatic application is disabled" in output:
                    self.show_update_notification("Updates are available. Automatic application is disabled in update_config.conf.", False)
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
                if stdout:
                    logging.warning(f"Update check error: {stdout}")
                    
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
                QTimer.singleShot(5000, self.restart_application)

                # Keep the non-modal dialog alive until it closes.
                msg_box.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                QTimer.singleShot(4000, msg_box.accept)
                
            else:
                # Info notification
                QMessageBox.information(
                    self,
                    "Update Information",
                    message
                )
                
        except Exception as e:
            logging.error(f"Error showing update notification: {e}")
    
    def restart_application(self):
        """Request a restart after the event loop and profile lock are released."""
        logging.info("Restarting application after automatic update...")
        app = QApplication.instance()
        app.setProperty("restartRequested", True)
        self.close()
        app.quit()


def acquire_instance_lock():
    """Protect this user's browser profile for the lifetime of the application."""
    data_dir = os.path.expanduser("~/.office_kiosk_data")
    os.makedirs(data_dir, mode=0o700, exist_ok=True)
    lock = QLockFile(os.path.join(data_dir, "instance.lock"))
    # A kiosk can run indefinitely. Only a dead owner should make its lock stale.
    lock.setStaleLockTime(0)
    if lock.tryLock(0):
        return lock
    if lock.error() == QLockFile.LockError.LockFailedError:
        logging.info("Office Kiosk Browser is already running for this user.")
        return None
    raise OSError(f"Cannot lock the browser profile: {lock.error().name}")


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
    is_rpi = KioskBrowser.detect_raspberry_pi()
    if is_rpi:
        # Qt6 WebEngine flags for better YouTube compatibility
        chromium_flags = [
            '--disable-software-rasterizer',
            '--enable-gpu-rasterization',
            '--ignore-gpu-blacklist',
            '--disable-dev-shm-usage',
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
    
    try:
        instance_lock = acquire_instance_lock()
    except OSError as error:
        logging.error("Cannot start Office Kiosk Browser: %s", error)
        return 1
    if instance_lock is None:
        return 0

    try:
        exit_code, restart_requested = run_application(is_rpi)
    finally:
        instance_lock.unlock()

    if restart_requested:
        # Replace this process only after Qt shutdown has released the profile lock.
        # Preserve the interpreter and command-line options on every platform.
        try:
            os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), *sys.argv[1:]])
        except OSError:
            logging.exception("Could not restart Office Kiosk Browser")
            return 1
    return exit_code


def run_application(is_rpi):
    """Run Qt while main() holds the profile lock, then return the restart request."""
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
    exit_code = app.exec()
    return exit_code, bool(app.property("restartRequested"))

if __name__ == "__main__":
    sys.exit(main())
