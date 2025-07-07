# Office Kiosk Browser

A touchscreen-friendly browser application designed for Raspberry Pi kiosks with quick access shortcuts to Home Assistant, YouTube Music, and other services. Features a modern, responsive design with robust error handling and debugging capabilities.

## 🚨 Quick Fix: "No module named PyQt5" Error

If you get this error when trying to start the kiosk, run these commands on your Raspberry Pi:

```bash
# Install PyQt5 system packages
sudo apt update
sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine

# Test if it works
python3 -c "import PyQt5.QtWidgets; print('PyQt5 OK')"

# Run the debugging script for more help
cd /home/pi/office_kiosk
chmod +x debug_startup.sh
./debug_startup.sh
```

## Features

- **Touch-Friendly Interface**: Large buttons and controls optimized for touchscreen use with proportional sizing
- **Responsive Design**: Automatically adapts to different screen sizes and resolutions
- **Quick Access Shortcuts**: Pre-configured buttons for:
  - 🏠 Home Assistant (with special error handling for local connections)
  - 🎵 YouTube Music  
  - 🔍 Google
  - 📺 YouTube
- **Full Browser Navigation**: Back, forward, refresh, home, and fullscreen buttons with visual feedback
- **Raspberry Pi Shutdown**: Safe shutdown button (⏻) appears automatically when running on Raspberry Pi hardware
- **Advanced Error Handling**: Detailed error messages and troubleshooting guidance, especially for Home Assistant connections
- **Debugging Features**: 
  - Comprehensive logging system
  - F12 developer tools toggle
  - Connection testing utilities
  - Debug information dialogs
- **Fullscreen Mode**: Perfect for kiosk displays with easy toggle
- **Beautiful Home Page**: Custom landing page with live clock and service descriptions
- **Scrollbar Support**: Enabled for proper navigation within web content
- **Cross-Platform**: Works on Windows (for testing) and Linux/Raspberry Pi

## Requirements

- Python 3.7 or higher
- PyQt5 and PyQtWebEngine

## Installation

### Windows (for testing)

1. Clone or download this repository
2. Run the setup script:
   ```cmd
   start_kiosk.bat
   ```

### Raspberry Pi / Linux

1. Clone or download this repository
2. Make the startup script executable:
   ```bash
   chmod +x start_kiosk.sh
   ```
3. Run the application:
   ```bash
   ./start_kiosk.sh
   ```

**Note:** When running on Raspberry Pi, the application automatically starts in fullscreen mode for optimal kiosk operation.

### Manual Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux: `source .venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python kiosk_browser.py
   ```

## Usage

### Basic Navigation
- Use the navigation buttons at the top: Back, Forward, Refresh, Home
- Click shortcut buttons for quick access to services

### Keyboard Shortcuts
- **F11**: Toggle fullscreen mode
- **Escape**: Exit fullscreen mode
- **F12**: Toggle developer tools for debugging
- **Ctrl+R**: Refresh page

### Advanced Features
- **Error Handling**: Automatic detection and helpful error messages for connection issues
- **Home Assistant Support**: Special handling for local Home Assistant connections with SSL certificate guidance
- **Logging**: Comprehensive logging system for debugging issues
- **Connection Testing**: Built-in utilities to test Home Assistant connectivity
- **Raspberry Pi Integration**: Automatic hardware detection with fullscreen mode and safe shutdown functionality
- **Auto-Update System**: Automatic version checking and updates from GitHub repository (Raspberry Pi only)

### Command Line Options
- `--fullscreen`: Start in fullscreen mode
  ```bash
  python kiosk_browser.py --fullscreen
  ```

## Configuration

The application is designed to work out-of-the-box with sensible defaults. Key configuration options:

- **Responsive Layout**: Automatically scales UI elements based on window size
- **Home Assistant URL**: Default is `http://homeassistant.local:8123` (easily customizable in code)
- **Shortcuts**: Pre-configured for common services, easily modifiable in the source code
- **Error Handling**: Built-in troubleshooting for common connection issues

## Troubleshooting

### Home Assistant Connection Issues

The application includes special handling for Home Assistant connections:

1. **Certificate Errors**: The app provides guidance for SSL certificate issues with local installations
2. **Network Connectivity**: Automatic detection of local network issues with helpful suggestions
3. **Connection Testing**: Built-in utilities to verify Home Assistant accessibility
4. **Error Messages**: Clear, actionable error messages with troubleshooting steps

### Common Solutions

- **Can't connect to Home Assistant**: 
  - Verify Home Assistant is running
  - Check if using correct URL (try both HTTP and HTTPS)
  - Ensure device is on same network
  - For SSL issues, try HTTP instead of HTTPS for local connections

- **Touch input issues**:
  - Verify touchscreen drivers are installed
  - Check Qt touchscreen support

- **UI elements too small/large**:
  - The app automatically scales based on window size
  - Try different window sizes or fullscreen mode

## Raspberry Pi Setup

For a dedicated kiosk setup on Raspberry Pi:

1. **Run the automated installer**:
   ```bash
   ./install_rpi.sh
   ```
   This will automatically set up autostart and all required dependencies.

2. **Ensure Pi boots to desktop** (Very Important!):
   ```bash
   sudo raspi-config
   # Navigate to: Boot Options -> Desktop/CLI -> Desktop Autologin
   ```

3. **Reboot to test autostart**:
   ```bash
   sudo reboot
   ```

### Autostart Troubleshooting

If the application doesn't start automatically after reboot:

1. **Check boot configuration**:
   - Ensure Raspberry Pi boots to desktop (not console)
   - Use `sudo raspi-config` -> Boot Options -> Desktop/CLI -> Desktop Autologin

2. **Run the troubleshooting script**:
   ```bash
   ./troubleshoot_autostart.sh
   ```

3. **Check autostart files**:
   ```bash
   # Check desktop autostart file
   cat ~/.config/autostart/kiosk-browser.desktop
   
   # Check systemd service status
   systemctl --user status kiosk-browser.service
   ```

4. **Manual testing**:
   ```bash
   # Test desktop file
   gtk-launch kiosk-browser.desktop
   
   # Test systemd service
   systemctl --user start kiosk-browser.service
   ```

5. **View logs**:
   ```bash
   # Check systemd service logs
   journalctl --user -u kiosk-browser.service
   
   # Check application logs
   tail -f /var/log/kiosk-update.log
   ```

### Manual Autostart Setup

If the automated installer doesn't work, you can set up autostart manually using one of these methods:

#### Method 1: Desktop Entry (Modern Pi OS)
```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/kiosk-browser.desktop << EOF
[Desktop Entry]
Type=Application
Name=Office Kiosk Browser
Exec=/path/to/office_kiosk/start_kiosk.sh
Path=/path/to/office_kiosk
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Terminal=false
EOF
```

#### Method 2: Legacy LXDE Autostart (Older Pi OS)
```bash
# Create LXDE autostart directory
mkdir -p ~/.config/lxsession/LXDE-pi

# Create or edit autostart file
cat > ~/.config/lxsession/LXDE-pi/autostart << EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@sh -c 'sleep 10 && cd /path/to/office_kiosk && /path/to/office_kiosk/start_kiosk.sh'
EOF
```

#### Method 3: Systemd User Service
```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/kiosk-browser.service << EOF
[Unit]
Description=Office Kiosk Browser
After=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=:0
WorkingDirectory=/path/to/office_kiosk
ExecStart=/path/to/office_kiosk/start_kiosk.sh
Restart=always

[Install]
WantedBy=default.target
EOF

# Enable the service
systemctl --user daemon-reload
systemctl --user enable kiosk-browser.service
```

**Note**: Replace `/path/to/office_kiosk` with the actual path to your installation directory.

**Note:** The startup script automatically detects Raspberry Pi hardware and enables fullscreen mode without requiring the `--fullscreen` parameter. A shutdown button (⏻) is also automatically added to safely power down the Pi.

### Configuring Shutdown Permissions

For the shutdown button to work properly on Raspberry Pi, you may need to configure sudo permissions:

```bash
# Allow the user to run shutdown without password
echo "$USER ALL=(ALL) NOPASSWD: /sbin/shutdown" | sudo tee /etc/sudoers.d/kiosk-shutdown
```

This allows the kiosk user to safely shutdown the Pi without entering a password.

## Auto-Update System (Raspberry Pi)

The kiosk browser includes an automatic update system that checks for new versions from the GitHub repository:

### Features:
- **Automatic Detection**: Checks for updates on every startup
- **Configurable**: Enable/disable automatic updates via configuration file
- **Safe Updates**: Creates backups before applying updates
- **Dependency Management**: Automatically updates Python dependencies when needed
- **Logging**: Comprehensive logging of all update activities

### Configuration:

Edit `update_config.conf` to customize update behavior:

```bash
# Enable automatic update checking (true/false)
AUTO_UPDATE_CHECK=true

# Apply updates automatically without user prompt (true/false)
AUTO_UPDATE_APPLY=false

# Maximum time to wait for update check (seconds)
UPDATE_TIMEOUT=30
```

### Manual Update Check:

```bash
# Check for updates manually
./update_check.sh

# View update logs
tail -f /var/log/kiosk-update.log
```

### Disabling Auto-Updates:

To disable automatic updates, edit `update_config.conf`:
```bash
AUTO_UPDATE_CHECK=false
```

## Customizing Shortcuts

To add or modify shortcuts, edit the `shortcuts` list in `kiosk_browser.py`:

```python
shortcuts = [
    ("🏠 HA", "http://homeassistant.local:8123", "#e74c3c"),
    ("🎵 YT Music", "https://music.youtube.com", "#e67e22"),
    ("� Google", "https://www.google.com", "#27ae60"),
    ("📺 YouTube", "https://www.youtube.com", "#c0392b"),
    # Add your custom shortcuts here
    ("�📊 Grafana", "http://your-grafana:3000", "#ff6b6b"),
]
```

Format: `(Display Name, URL, Hex Color)`

## Quick Start Debugging

If you're having issues getting the kiosk to start, use these diagnostic tools:

### 1. Run the Debugging Script
```bash
cd /home/pi/office_kiosk
chmod +x debug_startup.sh
./debug_startup.sh
```

This comprehensive script will check:
- PyQt5 installation and imports
- Project files and permissions
- Display environment (X11)
- System logs and errors
- Provides specific fixes for common issues

### 2. Setup Auto-Updates
```bash
cd /home/pi/office_kiosk
chmod +x setup_auto_update.sh
./setup_auto_update.sh
```

Choose option 1 to enable automatic updates every 30 minutes from GitHub.

## Display Support

### Touchscreen Displays
The kiosk browser is optimized for touchscreen displays:
- **Automatic resolution detection** and configuration
- **Responsive UI scaling** for different resolutions
- **Touch-friendly interface** design

### Different Display Resolutions
The application automatically adapts to different screen sizes with responsive design.

## Common Installation Issues

### "No module named PyQt5" Error

This is the most common issue. Here are the solutions:

**For Raspberry Pi OS (Recommended):**
```bash
# Install system packages (preferred method)
sudo apt update
sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine python3-pyqt5.qtwebkit

# If QtWebEngine isn't available, try QtWebKit
sudo apt install python3-pyqt5 python3-pyqt5.qtwebkit
```

**For other Linux distributions:**
```bash
# Ubuntu/Debian
sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine python3-pyqt5-dev

# CentOS/RHEL/Fedora
sudo dnf install python3-qt5 python3-qt5-webkit
```

**Using pip (fallback method):**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install PyQt5
pip install PyQt5 PyQtWebEngine

# If PyQtWebEngine fails, try:
pip install PyQt5 PyQtWebKit
```

**Test PyQt5 Installation:**
```bash
python3 -c "import PyQt5.QtWidgets; print('PyQt5 installation: SUCCESS')"
```

### Auto-Installation Script

The project includes an automatic installer for Raspberry Pi:
```bash
chmod +x install_rpi.sh
./install_rpi.sh
```

This script will automatically:
- Install required system packages
- Set up Python dependencies with fallback options
- Configure autostart
- Handle PyQt5 installation issues

## Advanced Features

### Debugging and Diagnostics

- **F12**: Opens developer tools for web debugging
- **Comprehensive Logging**: All activities logged with timestamps and severity levels
- **Error Dialogs**: User-friendly error messages with troubleshooting guidance
- **Connection Testing**: Built-in Home Assistant connectivity testing

### Responsive Design

- **Proportional Sizing**: All UI elements scale based on window dimensions
- **Touch-Friendly**: Large buttons and adequate spacing for finger navigation
- **Visual Feedback**: Button hover and press states for better user experience
- **Flexible Layout**: Adapts to different screen sizes and orientations

## Troubleshooting

### Home Assistant Connection Issues

The application includes comprehensive error handling for Home Assistant:

**Connection Failures:**
- Automatic detection of Home Assistant URLs
- Specific error messages with troubleshooting steps
- Guidance for SSL certificate issues
- Suggestions for HTTP vs HTTPS protocols

**Common Solutions:**
1. **"Failed to connect"**: 
   - Verify Home Assistant is running and accessible
   - Check network connectivity
   - Try accessing the URL in a regular browser first

2. **SSL Certificate Errors**:
   - For local installations, try HTTP instead of HTTPS
   - Check if Home Assistant has valid SSL certificates
   - Consider using IP address instead of hostname

3. **DNS Resolution Issues**:
   - Verify `homeassistant.local` resolves correctly
   - Try using the IP address directly
   - Check mDNS/Bonjour service is running

### General Troubleshooting

**Installation Issues:**

**Installation Issues:**

1. **PyQt5 installation fails**:
   - On Raspberry Pi: `sudo apt-get install python3-pyqt5 python3-pyqt5.qtwebengine`
   - On Ubuntu: `sudo apt-get install python3-pyqt5 python3-pyqt5.qtwebengine python3-pyqt5-dev`

2. **Application won't start**:
   - Check Python version (3.7+ required)
   - Verify all dependencies are installed: `pip install -r requirements.txt`
   - Check error logs for specific issues

**Performance Issues:**

3. **Slow loading or responsiveness**:
   - Ensure adequate system resources (2GB+ RAM recommended)
   - Close unnecessary applications
   - Check network connection speed

4. **UI scaling issues**:
   - The app uses responsive design - try different window sizes
   - For very small screens, use fullscreen mode
   - Check display scaling settings in your OS

### Debugging Tips

- **Enable Debug Mode**: The application logs all activities with timestamps
- **Use F12**: Open developer tools to debug web page issues
- **Check Logs**: Look for error messages in the console output
- **Test Connectivity**: Use the built-in connection testing features

### Performance Tips for Raspberry Pi

- Use a microSD card with good write speeds (Class 10 or better)
- Ensure adequate cooling for sustained operation
- Consider using Raspberry Pi 4 with 4GB+ RAM for best performance
- Close unnecessary services to free up memory

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:

1. **Check the troubleshooting section above** - Most common issues are covered
2. **Review the logs** - The application provides detailed logging for debugging
3. **Test connectivity** - Use F12 developer tools to diagnose web page issues
4. **Verify Home Assistant setup** - Ensure HA is accessible from other devices
5. **Check system requirements** - Ensure adequate hardware and software support

### Getting Help

- **Home Assistant Issues**: Verify your HA installation is working correctly
- **Network Problems**: Test connectivity using built-in debugging features  
- **UI Problems**: Try different window sizes and fullscreen mode
- **Performance**: Monitor system resources and close unnecessary applications

The application includes comprehensive error handling and debugging features to help identify and resolve most issues automatically.
