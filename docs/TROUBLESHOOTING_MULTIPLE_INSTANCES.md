# Office Kiosk Browser - Troubleshooting Multiple Instances

## Problem: Multiple Browser Windows Opening

If you're seeing multiple browser windows or instances of the Office Kiosk Browser, this is caused by having multiple autostart methods enabled simultaneously.

## Quick Diagnosis

Run this command to quickly identify all autostart sources:

```bash
./install/trace_autostart.sh
```

This will show you exactly which autostart methods are enabled and how many instances are currently running.

## Step-by-Step Fix

### 1. Check Current Status
```bash
./install/manage_autostart.sh status
```

This shows:
- How many instances are currently running
- Which autostart methods are enabled
- Detailed information about each autostart source

### 2. Stop All Running Instances
```bash
./install/manage_autostart.sh stop
```

This will:
- Stop all running browser instances
- Clean up virtual keyboard processes
- Ensure a clean state

### 3. Disable ALL Autostart Methods
```bash
./install/manage_autostart.sh disable
```

This removes autostart entries from:
- Desktop autostart (`~/.config/autostart/`)
- Systemd user services
- Shell initialization files (`.bashrc`, `.profile`, `.bash_profile`, `.xinitrc`, `.xsessionrc`)
- Crontab entries
- Old systemd services

**Note:** System-wide services (`/etc/systemd/system/`) require manual removal with sudo.

### 4. Enable Only One Autostart Method
```bash
./install/manage_autostart.sh enable
```

This sets up the recommended desktop autostart method.

### 5. Verify the Fix
```bash
./install/manage_autostart.sh status
```

Should show:
- ✅ Only 1 autostart method enabled
- Either 0 or 1 instance running

### 6. Test
Reboot your system and verify only one browser window opens.

## Advanced Debugging

### Detailed Process Information
```bash
./install/manage_autostart.sh debug
```

This provides:
- Detailed process tree
- Parent process information (helps identify autostart source)
- Process start times
- Recommendations based on findings

### Manual Investigation

Check specific files manually:

```bash
# Desktop autostart
ls -la ~/.config/autostart/*kiosk* 2>/dev/null

# Shell files
grep -n "kiosk\|office" ~/.bashrc ~/.profile ~/.bash_profile 2>/dev/null

# Systemd services
systemctl --user list-unit-files | grep kiosk
systemctl list-unit-files | grep kiosk

# Crontab
crontab -l | grep kiosk
```

## Common Autostart Locations

The script checks these locations for autostart entries:

### Primary (Recommended)
- `~/.config/autostart/office-kiosk-browser.desktop` - Desktop autostart

### Secondary (Should be disabled)
- `~/.config/systemd/user/office-kiosk-browser.service` - Systemd user service
- `~/.bashrc` - Bash shell startup
- `~/.profile` - Shell profile
- `~/.bash_profile` - Bash profile
- `~/.xinitrc` - X11 initialization
- `~/.xsessionrc` - X session startup
- Crontab entries
- `/etc/rc.local` - System startup script

### Legacy (Should be removed)
- `/etc/systemd/system/kiosk-browser.service` - Old system service
- `~/.config/systemd/user/kiosk-browser.service` - Old user service
- Any other variations of service names

## Prevention

To prevent this issue in the future:

1. **Only use one autostart method** - The desktop autostart is recommended
2. **Run status checks** after making changes: `./install/manage_autostart.sh status`
3. **Clean up properly** when testing different methods
4. **Use the management script** instead of manually editing files

## Emergency Reset

If the automatic tools don't work, manually remove all autostart sources:

```bash
# Remove desktop autostart
rm -f ~/.config/autostart/*kiosk* ~/.config/autostart/*office*

# Remove systemd services
systemctl --user disable office-kiosk-browser.service 2>/dev/null || true
systemctl --user stop office-kiosk-browser.service 2>/dev/null || true
rm -f ~/.config/systemd/user/*kiosk* ~/.config/systemd/user/*office*
systemctl --user daemon-reload

# Clean shell files (backup first!)
cp ~/.bashrc ~/.bashrc.backup
cp ~/.profile ~/.profile.backup 2>/dev/null || true
sed -i '/kiosk\|office.*browser/d' ~/.bashrc
sed -i '/kiosk\|office.*browser/d' ~/.profile 2>/dev/null || true

# Clean crontab
crontab -l | grep -v "kiosk\|office.*browser" | crontab -

# Stop all instances
pkill -f kiosk_browser.py
```

Then re-enable with:
```bash
./install/manage_autostart.sh enable
```

## Need Help?

If you're still experiencing issues:

1. Run `./install/trace_autostart.sh` and include the output when reporting issues
2. Check the main README.md for additional troubleshooting steps
3. Verify your system meets the requirements (Qt6, proper display server, etc.)
