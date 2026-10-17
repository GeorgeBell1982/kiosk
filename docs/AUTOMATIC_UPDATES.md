# Automatic Updates Documentation

## Overview

The Office Kiosk Browser now supports fully automatic updates with **no user prompts required**. When the application starts on a Raspberry Pi, it will:

1. Check for updates in the background
2. Automatically apply any available updates
3. Show a brief notification
4. Restart the application with the new version

## Configuration

Automatic updates are controlled by the configuration file: `scripts/update_config.conf`

### Key Settings

```bash
# Enable automatic update checking (true/false)
AUTO_UPDATE_CHECK=true

# Apply updates automatically without user prompt (true/false)
# When true, updates will be applied automatically with NO user interaction
AUTO_UPDATE_APPLY=true
```

With `AUTO_UPDATE_APPLY=false`, background and cron checks report available
updates without applying them. An interactive terminal can still offer a prompt.
`UPDATE_TIMEOUT` must be a positive integer and limits Git fetch time in seconds.

### Important Notes

- **Automatic updates only work on Raspberry Pi** - disabled on other platforms for safety
- **Git repository required** - the app must be in a git repository to receive updates
- **Background operation** - updates check in background, won't block app startup
- **Automatic restart** - app restarts automatically after updates are applied

## How It Works

### On Application Startup

1. **Platform Check**: Verifies running on Raspberry Pi
2. **Repository Check**: Confirms git repository exists
3. **Background Update Check**: Runs `scripts/update_check.sh` in background
4. **Progress Monitoring**: Checks update process status every few seconds

### When Updates Are Found

1. **Automatic Download**: Git fetches changes with a timeout, then applies the
   exact fetched commit using a fast-forward merge. Ahead or diverged local
   branches are skipped.
2. **Backup Creation**: Creates backup in `/tmp/kiosk-backup-[timestamp]/`
   before changing the checkout; backup failure aborts the update.
3. **Dependencies Update**: Checks the entire incoming commit range for dependency
   changes. A virtual environment uses `requirements-rpi.txt` when available,
   preserving system-installed Qt packages.
4. **Version Metadata**: Uses the version metadata supplied by the repository.
5. **Restart Flag**: Creates `/tmp/kiosk-restart-needed` flag file

If dependency installation fails, the updater reports failure without requesting
a restart. The checkout has already advanced; retry the logged pip command or
restore the backup before restarting the kiosk. Dependency installation is not
transactional.

### User Experience

1. **Brief Notification**: Shows dialog: "Updates have been applied automatically!"
2. **Auto-close**: Dialog auto-closes after 4 seconds
3. **Automatic Restart**: App restarts in 5 seconds with new version
4. **No Interaction Required**: Completely hands-off process

## Testing Automatic Updates

### Test Configuration

Run the test script to verify automatic updates are properly configured:

```bash
python tests/test_automatic_updates.py
```

This will check:
- Configuration file exists and is valid
- Update script exists
- Automatic settings are enabled
- Git repository is available
- Platform compatibility

### Manual Update Test

You can manually trigger the update process to test it:

```bash
./scripts/update_check.sh
```

On Raspberry Pi with `AUTO_UPDATE_APPLY=true`, this will apply updates automatically.

## Troubleshooting

### Updates Not Working

1. **Check Platform**: Automatic updates only work on Raspberry Pi
   ```bash
   cat /proc/cpuinfo | grep "Raspberry Pi"
   ```

2. **Check Git Repository**: Ensure you're in a git repository
   ```bash
   git status
   ```

3. **Check Configuration**: Verify settings in `scripts/update_config.conf`
   ```bash
   cat scripts/update_config.conf
   ```

4. **Check Internet**: Ensure internet connectivity
   ```bash
   git ls-remote origin main
   ```

5. **Check Logs**: Review update logs
   ```bash
   tail -f "${XDG_STATE_HOME:-$HOME/.local/state}/office-kiosk/update.log"
   ```

   Logging runs as the desktop user and never invokes `sudo`. Set `UPDATE_LOG`
   in `scripts/update_config.conf` to choose another writable log file.

### Common Issues

#### "Not a git repository"
- Ensure the app is cloned from git, not downloaded as ZIP
- Run `git init` and configure remote if needed

#### "Failed to fetch updates"
- Check internet connection
- Verify GitHub repository is accessible
- Check SSH keys or authentication

#### "Update check disabled"
- Set `AUTO_UPDATE_CHECK=true` in `scripts/update_config.conf`

#### "Updates require user prompt"
- Set `AUTO_UPDATE_APPLY=true` in `scripts/update_config.conf`

### Backup and Recovery

#### Automatic Backups
- Each update creates automatic backup in `/tmp/kiosk-backup-[timestamp]/`
- Backups include complete application directory
- Use backups to restore previous version if needed

#### Manual Backup
```bash
cp -r /path/to/office_kiosk /path/to/backup-$(date +%Y%m%d)
```

#### Restore from Backup
```bash
cp -r /tmp/kiosk-backup-[timestamp]/* /path/to/office_kiosk/
```

## Advanced Configuration

### Update Timeout
```bash
# Maximum time allowed for Git fetch (seconds)
UPDATE_TIMEOUT=30
```

### Logging Level
```bash
# Log level for update operations (INFO/DEBUG)
UPDATE_LOG_LEVEL=INFO
```

### Custom Update Script
You can modify `scripts/update_check.sh` to customize the update behavior, but ensure:
- Keep the `AUTO_UPDATE_APPLY` check
- Maintain the flag file creation (`/tmp/kiosk-restart-needed`)
- Preserve the output signals (`UPDATES_APPLIED_AUTOMATICALLY`)

## Security Considerations

- Updates are pulled from the configured git remote (origin/main)
- No arbitrary code execution from external sources
- Automatic backups provide rollback capability
- Updates only run on designated Raspberry Pi systems
- Process runs with same privileges as the application

## Benefits

✅ **Zero Maintenance**: No manual intervention required  
✅ **Always Current**: Automatic updates ensure latest features and security fixes  
✅ **Reliable**: Automatic backups and error handling  
✅ **User-Friendly**: Minimal disruption to user experience  
✅ **Secure**: Only pulls from trusted git repository  
✅ **Platform-Safe**: Only active on designated Raspberry Pi systems  

## Summary

With `AUTO_UPDATE_APPLY=true`, the Office Kiosk Browser will:
- ✅ Check for updates automatically on startup
- ✅ Download and apply updates without any prompts
- ✅ Show brief notification to user
- ✅ Restart automatically with new version
- ✅ Require absolutely no user interaction

This ensures your kiosk always runs the latest version with zero maintenance overhead.
