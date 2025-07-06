#!/usr/bin/env python3
"""
Office Kiosk Browser Application
A touchscreen-friendly browser with shortcuts for Home Assistant, YouTube Music, and Google.
Designed for Raspberry Pi but works on Windows for testing.
"""

import sys
import logging
import subprocess
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFrame, QMessageBox, QLabel)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QFont
from version import get_version_string, get_full_version_info

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class KioskBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Log version information
        version_info = get_full_version_info()
        logging.info(f"Starting Office Kiosk Browser {version_info['formatted']}")
        
        self.web_view = None  # Initialize early
        self.is_raspberry_pi = self.detect_raspberry_pi()
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
        self.setWindowTitle("Office Kiosk Browser")
        self.setGeometry(100, 100, 1024, 768)
        
        # Set up the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create web view first
        self.web_view = QWebEngineView()
        
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
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                margin: 2px;
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
        
    def create_control_panel(self, main_layout):
        """Create the control panel with controls on left and shortcuts on right"""
        control_frame = QFrame()
        # Use percentage of window height instead of fixed pixels
        window_height = self.height()
        window_width = self.width()
        control_height = max(100, int(window_height * 0.15))  # 15% of window height, minimum 100px
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
        version_label = QLabel(version_info['formatted'], control_frame)
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
        version_label.move(25, 0)  # Position with more spacing from edge and move up 5 more pixels
        version_label.adjustSize()  # Resize to fit content
        
        # Left side - Navigation controls group
        nav_controls_group = QFrame()
        # Use percentage of window width instead of fixed pixels
        # Make navigation wider on Raspberry Pi to accommodate shutdown button
        nav_width_percent = 0.5 if self.is_raspberry_pi else 0.4  # 50% vs 40% of window width
        nav_width = int(window_width * nav_width_percent)
        nav_hight = int(window_height * 0.10)  # 10% of window hight
        nav_controls_group.setFixedWidth(nav_width)
        nav_controls_group.setFixedHeight(nav_hight)
        nav_controls_group.setStyleSheet("""
            QFrame {
                background-color: rgba(44, 62, 80, 0.8);
                border-radius: 15px;
                margin: 2px;
                padding: 5px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        nav_controls_layout = QHBoxLayout()
        nav_controls_layout.setSpacing(15)  # More spacing for larger buttons
        nav_controls_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins for maximum button space
        nav_controls_group.setLayout(nav_controls_layout)
        
        # Navigation buttons - consistent sizing with proportional fonts
        font_size = max(16, int(control_height * 0.10))  # Font size based on control height
        nav_button_style = f"""
            QPushButton {{
                background-color: #3498db;
                border: none;
                color: white;
                font-size: {font_size}px;
                font-weight: bold;
                border-radius: 12px;
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
        
        # Create navigation buttons with proportional size
        # Button size based on control frame dimensions
        button_width = int(control_height * 0.6)  # 70% of control height
        button_height = int(control_height * 0.45)  # 60% of control height
        button_size = (button_width, button_height)
        
        self.back_btn = QPushButton("←")
        self.back_btn.clicked.connect(self.web_view.back)
        self.back_btn.setFixedSize(*button_size)
        self.back_btn.setStyleSheet(nav_button_style)
        
        self.forward_btn = QPushButton("→")
        self.forward_btn.clicked.connect(self.web_view.forward)
        self.forward_btn.setFixedSize(*button_size)
        self.forward_btn.setStyleSheet(nav_button_style)
        
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.clicked.connect(self.web_view.reload)
        self.refresh_btn.setFixedSize(*button_size)
        self.refresh_btn.setStyleSheet(nav_button_style)
        
        self.home_btn = QPushButton("🏠")
        self.home_btn.clicked.connect(self.load_home_page)
        self.home_btn.setFixedSize(*button_size)
        self.home_btn.setStyleSheet(nav_button_style)
        
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setFixedSize(*button_size)
        self.fullscreen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #9b59b6;
                border: none;
                color: white;
                font-size: {max(18, int(font_size * 0.9))}px;
                font-weight: bold;
                border-radius: 12px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: #8e44ad;
            }}
            QPushButton:pressed {{
                background-color: #732d91;
            }}
        """)
        
        nav_controls_layout.addWidget(self.back_btn)
        nav_controls_layout.addWidget(self.forward_btn)
        nav_controls_layout.addWidget(self.refresh_btn)
        nav_controls_layout.addWidget(self.home_btn)
        nav_controls_layout.addWidget(self.fullscreen_btn)
        
        # Add shutdown button only on Raspberry Pi
        if self.is_raspberry_pi:
            self.shutdown_btn = QPushButton("⏻")
            self.shutdown_btn.clicked.connect(self.shutdown_pi)
            self.shutdown_btn.setFixedSize(*button_size)
            self.shutdown_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #e74c3c;
                    border: none;
                    color: white;
                    font-size: {max(18, int(font_size * 0.9))}px;
                    font-weight: bold;
                    border-radius: 12px;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: #c0392b;
                }}
                QPushButton:pressed {{
                    background-color: #a93226;
                }}
            """)
            nav_controls_layout.addWidget(self.shutdown_btn)
            logging.info("Raspberry Pi detected - shutdown button added")
        
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
        shortcuts_layout = QHBoxLayout()
        shortcuts_layout.setSpacing(15)  # More spacing for larger buttons
        shortcuts_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins for maximum button space
        shortcuts_group.setLayout(shortcuts_layout)
        
        # Define shortcuts with their URLs
        shortcuts = [
            ("🏠 HA", "http://homeassistant.local:8123", "#e74c3c"),
            ("🎵 YT Music", "https://music.youtube.com", "#e67e22"),
            ("🔍 Google", "https://www.google.com", "#27ae60"),
            ("📺 YouTube", "https://www.youtube.com", "#c0392b")
        ]
        
        self.shortcut_buttons = []
        for name, url, color in shortcuts:
            btn = QPushButton(name)
            # Proportional sizing for shortcut buttons
            shortcut_width = int(window_width * 0.15)  # 15% of window width
            shortcut_height = button_height  # Same height as nav buttons
            shortcut_font_size = max(12, int(control_height * 0.15))  # Smaller font for text buttons
            btn.setFixedSize(shortcut_width, shortcut_height)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: none;
                    color: white;
                    padding: 12px;
                    font-size: {shortcut_font_size}px;
                    font-weight: bold;
                    border-radius: 12px;
                    margin: 2px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                QPushButton:hover {{
                    background-color: {self.darken_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(self.darken_color(color))};
                }}
            """)
            btn.clicked.connect(lambda checked, u=url: self.load_url(u))
            shortcuts_layout.addWidget(btn)
            self.shortcut_buttons.append(btn)
        
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
        """Configure the web view settings"""
        settings = self.web_view.settings()
        
        # Enable various web features
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        
        # Connect URL change signal
        self.web_view.urlChanged.connect(self.on_url_changed)
        
        # Connect loading signals
        self.web_view.loadStarted.connect(self.on_load_started)
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.web_view.loadProgress.connect(self.on_load_progress)
        
        # Enable debugging for web engine
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, True)  # Enable scrollbars for content navigation
        
        # Enable local content access for better local network support
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        
        # Connect certificate error handling - use the page's profile
        page = self.web_view.page()
        if hasattr(page, 'profile'):
            profile = page.profile()
            if hasattr(profile, 'requestIntercepted'):
                # Alternative approach: handle through request interception
                logging.info("Using request interception for SSL handling")
        
        logging.info("Web view setup complete")
        
    def load_home_page(self):
        """Load the default home page"""
        # Create a simple HTML home page
        home_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Office Kiosk - Home</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
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
                    margin-bottom: 30px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                .welcome {
                    font-size: 1.5em;
                    margin-bottom: 40px;
                    opacity: 0.9;
                }
                .shortcuts-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 40px;
                }
                .shortcut-card {
                    background: rgba(255,255,255,0.1);
                    border-radius: 15px;
                    padding: 30px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                    transition: transform 0.3s ease;
                }
                .shortcut-card:hover {
                    transform: translateY(-5px);
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
                <h1>🏢 Office Kiosk</h1>
                <div class="welcome">Welcome! Use the shortcuts above to navigate to your favorite services.</div>
                <div class="time" id="current-time"></div>
                
                <div class="shortcuts-grid">
                    <div class="shortcut-card">
                        <h3>🏠 Home Assistant</h3>
                        <p>Control your smart home devices and automations</p>
                    </div>
                    <div class="shortcut-card">
                        <h3>🎵 YouTube Music</h3>
                        <p>Stream your favorite music and playlists</p>
                    </div>
                    <div class="shortcut-card">
                        <h3>🔍 Google</h3>
                        <p>Search the web and access Google services</p>
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
            </script>
        </body>
        </html>
        """
        
        self.web_view.setHtml(home_html)
        
    def load_url(self, url):
        """Load a specific URL"""
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
        self.refresh_btn.setText("⌛")
        
    def on_load_finished(self, success):
        """Called when page finishes loading"""
        current_url = self.web_view.url().toString()
        if success:
            logging.info(f"Page loaded successfully: {current_url}")
            self.refresh_btn.setText("⟳")
        else:
            logging.error(f"Page failed to load: {current_url}")
            self.refresh_btn.setText("⟳")
            
            # Handle specific error cases
            if "homeassistant" in current_url.lower():
                self.handle_network_error(current_url)
            else:
                QMessageBox.warning(self, "Load Error", f"Failed to load the page: {current_url}")
            
        # Additional debugging: check if it's a network error
        page = self.web_view.page()
        if hasattr(page, 'profile'):
            profile = page.profile()
            if hasattr(profile, 'httpUserAgent'):
                logging.info(f"User agent: {profile.httpUserAgent()}")
                
    def on_load_progress(self, progress):
        """Called during page loading to show progress"""
        logging.debug(f"Load progress: {progress}%")
        if progress < 100:
            self.refresh_btn.setText(f"⌛{progress}%")
            
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
6. For HTTPS with self-signed certificates, try adding --ignore-certificate-errors

Would you like to try a different URL?
            """
            QMessageBox.warning(self, "Home Assistant Connection Error", error_msg)
        else:
            QMessageBox.warning(self, "Network Error", f"Failed to connect to {url}")
            
    def test_home_assistant_connection(self):
        """Test if Home Assistant is accessible"""
        import socket
        try:
            # Try to resolve homeassistant.local
            host = "homeassistant.local"
            port = 8123
            socket.getaddrinfo(host, port)
            logging.info(f"DNS resolution successful for {host}")
            
            # Try to connect to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logging.info(f"Port {port} is open on {host}")
                return True
            else:
                logging.warning(f"Port {port} is not accessible on {host}")
                return False
                
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
            
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        if self.isFullScreen():
            self.showNormal()
            # Button text stays the same since it's just an icon
        else:
            self.showFullScreen()
            # Button text stays the same since it's just an icon
            
    def shutdown_pi(self):
        """Safely shutdown the Raspberry Pi"""
        if not self.is_raspberry_pi:
            QMessageBox.warning(self, "Not Available", "Shutdown button is only available on Raspberry Pi.")
            return
            
        reply = QMessageBox.question(
            self,
            "Shutdown Raspberry Pi",
            "Are you sure you want to shutdown the Raspberry Pi?\n\nThis will turn off the device completely.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
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
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
            # Button text stays the same since it's just an icon
        elif event.key() == Qt.Key_F12:
            # Toggle dev tools for debugging
            self.toggle_dev_tools()
        elif event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_R:
                self.web_view.reload()
        super().keyPressEvent(event)
        
    def toggle_dev_tools(self):
        """Toggle developer tools for debugging"""
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
            
    def show_debug_info(self):
        """Show debug information about the current page"""
        current_url = self.web_view.url().toString()
        page_title = self.web_view.page().title()
        
        debug_info = f"""
Debug Information:
- Current URL: {current_url}
- Page Title: {page_title}
- User Agent: {self.web_view.page().profile().httpUserAgent()}
- Qt Version: {Qt.qVersion()}
        """
        
        logging.info(debug_info)
        QMessageBox.information(self, "Debug Info", debug_info)

def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Office Kiosk Browser")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Office Kiosk")
    
    # Create and show the main window
    browser = KioskBrowser()
    
    # Check if we should start in fullscreen (useful for Raspberry Pi)
    if len(sys.argv) > 1 and sys.argv[1] == '--fullscreen':
        browser.showFullScreen()
    else:
        browser.show()
    
    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
