# Utility Scripts

Helper scripts for system configuration, startup, and maintenance.

## Startup Scripts

- `start_kiosk.sh` - Linux/Pi startup script
- `start_kiosk.bat` - Windows batch file  
- `start_kiosk.ps1` - Windows PowerShell script

Startup launchers use the project virtual environment when it exists, otherwise
system Python. Install dependencies before starting. Launch failures propagate as
nonzero exit codes; no launcher installs packages, changes display settings, or
waits for keyboard input. Linux startup uses `exec` so signals reach the browser.

## System Configuration

- `setup_waveshare.sh` - Configure Waveshare touchscreen displays
- `fix_pi_graphics.sh` - Fix common Pi graphics/display issues
- `fix_autostart_paths.sh` - Repair autostart configuration paths

## Maintenance & Updates

- `setup_auto_update.sh` - Configure automatic updates
- `update_check.sh` - Manual update checker
- `restore_config_backup.sh` - Restore configuration from backup

## Troubleshooting

- `debug_startup.sh` - Debug application startup issues
- `troubleshoot_autostart.sh` - Fix autostart problems

## Configuration

- `update_config.conf` - Update system configuration file

## Usage

Most scripts can be run directly:
```bash
chmod +x script_name.sh
./script_name.sh
```

For system-level changes, some scripts may require sudo privileges.
