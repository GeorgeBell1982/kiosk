# System Integration Files

System-level configuration files for auto-start and desktop integration.

## Systemd Services

### `kiosk-browser.service`
System-wide service that starts the browser on boot.

**Installation:**
```bash
sudo cp kiosk-browser.service /etc/systemd/system/
sudo systemctl enable kiosk-browser.service
sudo systemctl start kiosk-browser.service
```

### `kiosk-browser-user.service`
User-level service for single-user installations.

**Installation:**
```bash
cp kiosk-browser-user.service ~/.config/systemd/user/
systemctl --user enable kiosk-browser-user.service
systemctl --user start kiosk-browser-user.service
```

## Desktop Integration

### `Office Kiosk Browser.desktop`
Desktop entry file for application menu integration.

**Installation:**
```bash
cp "Office Kiosk Browser.desktop" ~/.local/share/applications/
# Or system-wide:
sudo cp "Office Kiosk Browser.desktop" /usr/share/applications/
```

## Usage Notes

**System Service (Recommended for kiosks):**
- Starts automatically on boot
- Runs with root privileges
- Best for dedicated kiosk machines

**User Service:**
- Starts when user logs in
- Runs with user privileges  
- Better for multi-user systems

**Desktop Entry:**
- Adds browser to application menu
- Allows manual startup from GUI
- Works alongside services
