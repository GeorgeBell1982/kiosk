#!/bin/bash

# Restore config.txt backup script
# This script helps restore the original config.txt from a backup created by setup_waveshare.sh

set -e

echo "=== RESTORE CONFIG.TXT BACKUP ==="
echo "This script will help restore your original /boot/config.txt"
echo "⚠️  WARNING: This will overwrite your current /boot/config.txt"
echo ""

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    echo "Running with root privileges ✅"
elif sudo -n true 2>/dev/null; then
    echo "Running with sudo privileges ✅"
else
    echo "❌ This script requires sudo privileges"
    echo "Please run: sudo $0"
    exit 1
fi

BOOT_CONFIG="/boot/config.txt"

# Check if config.txt exists
if [[ ! -f "$BOOT_CONFIG" ]]; then
    echo "❌ /boot/config.txt not found"
    echo "Are you running this on a Raspberry Pi?"
    exit 1
fi

# Find backup files
echo "Looking for config.txt backup files..."
BACKUP_FILES=($(find /boot -name "config.txt.backup.*" -type f 2>/dev/null | sort -r))

if [[ ${#BACKUP_FILES[@]} -eq 0 ]]; then
    echo "❌ No backup files found"
    echo "Expected files like: /boot/config.txt.backup.YYYYMMDD-HHMMSS"
    echo ""
    echo "If you have a manual backup, you can restore it with:"
    echo "sudo cp /path/to/your/backup /boot/config.txt"
    exit 1
fi

echo "Found ${#BACKUP_FILES[@]} backup file(s):"
echo ""

# List available backups
for i in "${!BACKUP_FILES[@]}"; do
    file="${BACKUP_FILES[$i]}"
    timestamp=$(basename "$file" | sed 's/config.txt.backup.//')
    size=$(stat -c%s "$file" 2>/dev/null || echo "unknown")
    date_created=$(stat -c%y "$file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1 || echo "unknown")
    
    echo "[$((i+1))] $(basename "$file")"
    echo "    Created: $date_created"
    echo "    Size: $size bytes"
    echo ""
done

# Get current config.txt info
current_size=$(stat -c%s "$BOOT_CONFIG" 2>/dev/null || echo "unknown")
current_date=$(stat -c%y "$BOOT_CONFIG" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1 || echo "unknown")

echo "Current /boot/config.txt:"
echo "    Modified: $current_date"
echo "    Size: $current_size bytes"
echo ""

# Ask user which backup to restore
echo "Which backup would you like to restore?"
echo "Enter the number (1-${#BACKUP_FILES[@]}), or 'q' to quit:"
read -r choice

if [[ "$choice" == "q" || "$choice" == "Q" ]]; then
    echo "Cancelled by user"
    exit 0
fi

# Validate choice
if ! [[ "$choice" =~ ^[0-9]+$ ]] || [[ "$choice" -lt 1 ]] || [[ "$choice" -gt ${#BACKUP_FILES[@]} ]]; then
    echo "❌ Invalid choice: $choice"
    exit 1
fi

# Get selected backup file
selected_backup="${BACKUP_FILES[$((choice-1))]}"
backup_name=$(basename "$selected_backup")

echo ""
echo "You selected: $backup_name"
echo ""

# Confirm restoration
echo "⚠️  FINAL WARNING ⚠️"
echo "This will:"
echo "  1. Backup current /boot/config.txt to /boot/config.txt.pre-restore.$(date +%Y%m%d-%H%M%S)"
echo "  2. Replace /boot/config.txt with $backup_name"
echo "  3. You will need to reboot for changes to take effect"
echo ""
echo "Do you want to continue? (yes/no):"
read -r confirm

if [[ "$confirm" != "yes" ]]; then
    echo "Cancelled by user"
    exit 0
fi

echo ""
echo "=== RESTORING BACKUP ==="

# Create a backup of current config before restoring
current_backup="/boot/config.txt.pre-restore.$(date +%Y%m%d-%H%M%S)"
echo "1. Creating backup of current config.txt..."
sudo cp "$BOOT_CONFIG" "$current_backup"
echo "✅ Current config backed up to: $current_backup"

# Restore the selected backup
echo "2. Restoring $backup_name..."
sudo cp "$selected_backup" "$BOOT_CONFIG"
echo "✅ Restored $backup_name to /boot/config.txt"

# Verify restoration
if [[ -f "$BOOT_CONFIG" ]]; then
    restored_size=$(stat -c%s "$BOOT_CONFIG")
    echo "✅ Verification: /boot/config.txt exists (${restored_size} bytes)"
else
    echo "❌ Error: /boot/config.txt not found after restoration"
    exit 1
fi

echo ""
echo "=== RESTORATION COMPLETE ==="
echo "✅ Successfully restored /boot/config.txt from backup"
echo ""
echo "Next steps:"
echo "1. Reboot your Raspberry Pi for changes to take effect:"
echo "   sudo reboot"
echo ""
echo "2. If you need to restore the Waveshare settings again later:"
echo "   ./setup_waveshare.sh"
echo ""
echo "3. If something goes wrong, you can restore the pre-restore backup:"
echo "   sudo cp $current_backup /boot/config.txt"
echo ""
