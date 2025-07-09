#!/usr/bin/env python3
"""
Test script to verify Home Assistant login persistence and Qt6 WebEngine storage configuration
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from PyQt6.QtCore import QUrl, QTimer

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class StorageTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Home Assistant Storage Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Info label
        self.info_label = QLabel("Testing Home Assistant login persistence...")
        layout.addWidget(self.info_label)
        
        # Control buttons
        btn_layout = QVBoxLayout()
        
        self.test_storage_btn = QPushButton("Test Storage Configuration")
        self.test_storage_btn.clicked.connect(self.test_storage_config)
        btn_layout.addWidget(self.test_storage_btn)
        
        self.load_ha_btn = QPushButton("Load Home Assistant (replace with your URL)")
        self.load_ha_btn.clicked.connect(self.load_home_assistant)
        btn_layout.addWidget(self.load_ha_btn)
        
        self.check_cookies_btn = QPushButton("Check Stored Cookies")
        self.check_cookies_btn.clicked.connect(self.check_cookies)
        btn_layout.addWidget(self.check_cookies_btn)
        
        self.clear_storage_btn = QPushButton("Clear All Storage (for testing)")
        self.clear_storage_btn.clicked.connect(self.clear_storage)
        btn_layout.addWidget(self.clear_storage_btn)
        
        layout.addLayout(btn_layout)
        
        # Web view
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Setup web engine with the same configuration as the main app
        self.setup_web_engine()
        
        # Timer for periodic checks
        self.timer = QTimer()
        self.timer.timeout.connect(self.periodic_check)
        self.timer.start(5000)  # Check every 5 seconds
        
    def setup_web_engine(self):
        """Configure WebEngine with the same settings as the main app"""
        settings = self.web_view.settings()
        
        # Enable all the same settings as the main app
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, False)
        
        # Configure profile for persistent storage
        profile = self.web_view.page().profile()
        
        # Use the same data directory as the main app
        data_dir = os.path.expanduser("~/.office_kiosk_data")
        cache_dir = os.path.join(data_dir, "cache")
        downloads_dir = os.path.join(data_dir, "downloads")
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(downloads_dir, exist_ok=True)
        
        profile.setPersistentStoragePath(data_dir)
        profile.setCachePath(cache_dir)
        profile.setDownloadPath(downloads_dir)
        
        # Force persistent cookies
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        
        # Configure HTTP cache
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        profile.setHttpCacheMaximumSize(100 * 1024 * 1024)  # 100MB
        
        # Set user agent
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 OfficeKiosk/1.0"
        )
        profile.setHttpUserAgent(user_agent)
        
        logging.info("WebEngine configured with persistent storage")
        
    def test_storage_config(self):
        """Test the storage configuration"""
        profile = self.web_view.page().profile()
        
        info = []
        info.append("=== Storage Configuration Test ===")
        info.append(f"Persistent Storage Path: {profile.persistentStoragePath()}")
        info.append(f"Cache Path: {profile.cachePath()}")
        info.append(f"Download Path: {profile.downloadPath()}")
        info.append(f"Cookies Policy: {profile.persistentCookiesPolicy()}")
        info.append(f"Cache Type: {profile.httpCacheType()}")
        info.append(f"Cache Max Size: {profile.httpCacheMaximumSize()} bytes")
        info.append(f"User Agent: {profile.httpUserAgent()}")
        
        # Check if directories exist and are writable
        data_dir = profile.persistentStoragePath()
        cache_dir = profile.cachePath()
        
        info.append("\n=== Directory Status ===")
        info.append(f"Data dir exists: {os.path.exists(data_dir)}")
        info.append(f"Data dir writable: {os.access(data_dir, os.W_OK) if os.path.exists(data_dir) else False}")
        info.append(f"Cache dir exists: {os.path.exists(cache_dir)}")
        info.append(f"Cache dir writable: {os.access(cache_dir, os.W_OK) if os.path.exists(cache_dir) else False}")
        
        # List storage files
        if os.path.exists(data_dir):
            try:
                files = os.listdir(data_dir)
                info.append(f"\nStorage files: {len(files)} files")
                for file in files[:10]:  # Show first 10 files
                    file_path = os.path.join(data_dir, file)
                    size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                    info.append(f"  {file} ({size} bytes)")
                if len(files) > 10:
                    info.append(f"  ... and {len(files) - 10} more files")
            except Exception as e:
                info.append(f"Error listing storage files: {e}")
        
        result = "\n".join(info)
        self.info_label.setText(result)
        logging.info(result)
        
    def load_home_assistant(self):
        """Load Home Assistant - replace with your actual URL"""
        # Replace this with your actual Home Assistant URL
        ha_url = "https://demo.home-assistant.io"  # Demo instance for testing
        
        self.info_label.setText(f"Loading Home Assistant: {ha_url}\nTry logging in and then restart this test to see if login persists.")
        self.web_view.load(QUrl(ha_url))
        logging.info(f"Loading Home Assistant: {ha_url}")
        
    def check_cookies(self):
        """Check stored cookies"""
        # Note: Qt6 WebEngine doesn't provide direct access to cookies
        # But we can check if the storage directory has cookie files
        profile = self.web_view.page().profile()
        data_dir = profile.persistentStoragePath()
        
        info = ["=== Cookie Storage Check ==="]
        
        if os.path.exists(data_dir):
            cookie_files = []
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if 'cookie' in file.lower() or 'session' in file.lower():
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        rel_path = os.path.relpath(file_path, data_dir)
                        cookie_files.append(f"  {rel_path} ({size} bytes)")
            
            if cookie_files:
                info.append(f"Found {len(cookie_files)} cookie/session files:")
                info.extend(cookie_files)
            else:
                info.append("No cookie files found - this might indicate an issue")
        else:
            info.append("Storage directory not found!")
        
        # Check WebEngine storage
        info.append(f"\nProfile Storage Path: {data_dir}")
        info.append(f"Profile is off-the-record: {profile.isOffTheRecord()}")
        
        result = "\n".join(info)
        self.info_label.setText(result)
        logging.info(result)
        
    def clear_storage(self):
        """Clear all storage for testing"""
        profile = self.web_view.page().profile()
        data_dir = profile.persistentStoragePath()
        
        try:
            # Clear the profile's storage
            profile.clearAllVisitedLinks()
            
            # Also try to remove files manually
            import shutil
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
                os.makedirs(data_dir, exist_ok=True)
                
            self.info_label.setText("Storage cleared! You can now test fresh login persistence.")
            logging.info("Storage cleared successfully")
            
        except Exception as e:
            error_msg = f"Error clearing storage: {e}"
            self.info_label.setText(error_msg)
            logging.error(error_msg)
            
    def periodic_check(self):
        """Periodic check of storage status"""
        profile = self.web_view.page().profile()
        data_dir = profile.persistentStoragePath()
        
        if os.path.exists(data_dir):
            try:
                files = os.listdir(data_dir)
                total_size = 0
                for file in files:
                    file_path = os.path.join(data_dir, file)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                
                # Update window title with storage info
                self.setWindowTitle(f"HA Storage Test - {len(files)} files, {total_size} bytes")
                
            except Exception as e:
                logging.debug(f"Error in periodic check: {e}")

def main():
    app = QApplication(sys.argv)
    
    # Set application properties for better storage
    app.setApplicationName("HomeAssistantStorageTest")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("OfficeKiosk")
    
    window = StorageTestWindow()
    window.show()
    
    # Run initial storage test
    QTimer.singleShot(1000, window.test_storage_config)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
