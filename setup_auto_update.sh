#!/bin/bash
# Setup auto-update checking for Office Kiosk Browser

echo "Office Kiosk Browser - Auto-Update Setup"
echo "========================================"
echo

SCRIPT_DIR="$(dirname "$0")"
UPDATE_SCRIPT="$SCRIPT_DIR/update_check.sh"
CRON_ENTRY="*/30 * * * * $UPDATE_SCRIPT >/dev/null 2>&1"

# Check if update script exists
if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo "✗ Update script not found: $UPDATE_SCRIPT"
    exit 1
fi

# Make update script executable
chmod +x "$UPDATE_SCRIPT"
echo "✓ Made update script executable"

# Function to setup cron job
setup_cron() {
    echo "Setting up cron job for auto-updates..."
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$UPDATE_SCRIPT"; then
        echo "⚠ Cron job already exists for update script"
        echo "Current cron jobs:"
        crontab -l 2>/dev/null | grep "$UPDATE_SCRIPT"
        echo
        read -p "Replace existing cron job? (y/n): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Keeping existing cron job"
            return
        fi
        
        # Remove existing cron job
        crontab -l 2>/dev/null | grep -v "$UPDATE_SCRIPT" | crontab -
        echo "✓ Removed existing cron job"
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✓ Added cron job: $CRON_ENTRY"
    echo "  Auto-update will check every 30 minutes"
}

# Function to show status
show_status() {
    echo "=== AUTO-UPDATE STATUS ==="
    
    if [ -f "$UPDATE_SCRIPT" ]; then
        echo "✓ Update script exists: $UPDATE_SCRIPT"
        if [ -x "$UPDATE_SCRIPT" ]; then
            echo "✓ Update script is executable"
        else
            echo "✗ Update script is not executable"
        fi
    else
        echo "✗ Update script missing"
    fi
    
    echo
    echo "Current cron jobs related to updates:"
    if crontab -l 2>/dev/null | grep -q "update_check\|office_kiosk"; then
        crontab -l 2>/dev/null | grep "update_check\|office_kiosk"
    else
        echo "  No auto-update cron jobs found"
    fi
    
    echo
    echo "Update configuration:"
    CONFIG_FILE="$SCRIPT_DIR/update_config.conf"
    if [ -f "$CONFIG_FILE" ]; then
        echo "✓ Config file exists: $CONFIG_FILE"
        echo "  Contents:"
        cat "$CONFIG_FILE" | sed 's/^/    /'
    else
        echo "✗ Config file missing: $CONFIG_FILE"
    fi
}

# Function to test update check
test_update() {
    echo "=== TESTING UPDATE CHECK ==="
    echo "Running update check manually..."
    
    cd "$SCRIPT_DIR"
    if [ -x "$UPDATE_SCRIPT" ]; then
        echo "Command: $UPDATE_SCRIPT"
        "$UPDATE_SCRIPT"
        echo "✓ Update check completed"
    else
        echo "✗ Cannot run update script (not executable)"
        echo "Fix with: chmod +x $UPDATE_SCRIPT"
    fi
}

# Function to disable auto-update
disable_auto_update() {
    echo "Disabling auto-update..."
    
    if crontab -l 2>/dev/null | grep -q "$UPDATE_SCRIPT"; then
        crontab -l 2>/dev/null | grep -v "$UPDATE_SCRIPT" | crontab -
        echo "✓ Removed auto-update cron job"
    else
        echo "⚠ No auto-update cron job found"
    fi
}

# Main menu
echo "Choose an option:"
echo "1. Setup auto-update (every 30 minutes)"
echo "2. Show auto-update status"
echo "3. Test update check manually"
echo "4. Disable auto-update"
echo "5. Exit"
echo

read -p "Choose an option (1-5): " -r choice

case $choice in
    1)
        setup_cron
        echo
        echo "✓ Auto-update setup complete!"
        echo "  Updates will be checked every 30 minutes"
        echo "  Logs are written to: $SCRIPT_DIR/update.log"
        ;;
    
    2)
        show_status
        ;;
    
    3)
        test_update
        ;;
    
    4)
        disable_auto_update
        ;;
    
    5)
        echo "No changes made."
        ;;
    
    *)
        echo "Invalid option. No changes made."
        ;;
esac

echo
echo "=== USEFUL COMMANDS ==="
echo "View update logs: tail -f $SCRIPT_DIR/update.log"
echo "Check cron jobs: crontab -l"
echo "Manual update check: cd $SCRIPT_DIR && ./update_check.sh"
echo "View system logs: journalctl --since '1 hour ago' | grep -i update"
