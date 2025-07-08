#!/bin/bash
# Auto-update script for Office Kiosk Browser
# Checks for updates from GitHub repository and prompts for update

REPO_URL="https://github.com/GeorgeBell1982/kiosk.git"
UPDATE_LOG="/var/log/kiosk-update.log"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/update_config.conf"

# Change to script directory to ensure we're in the right place
cd "$SCRIPT_DIR"

# Default configuration
AUTO_UPDATE_CHECK=true
AUTO_UPDATE_APPLY=false
UPDATE_TIMEOUT=30
UPDATE_LOG_LEVEL=INFO

# Load configuration if file exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | sudo tee -a "$UPDATE_LOG"
}

# Function to check internet connectivity
check_internet() {
    if ping -c 1 -W 2 github.com >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check for updates
check_for_updates() {
    cd "$SCRIPT_DIR"
    
    log_message "Checking for updates..."
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        log_message "Not a git repository. Skipping update check."
        return 1
    fi
    
    # Fetch latest changes
    if ! git fetch origin main >/dev/null 2>&1; then
        log_message "Failed to fetch updates from remote repository"
        return 1
    fi
    
    # Check if we're behind
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)
    
    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        log_message "Updates available! Local: $LOCAL_COMMIT, Remote: $REMOTE_COMMIT"
        return 0
    else
        log_message "Already up to date"
        return 1
    fi
}

# Function to update version number
update_version() {
    cd "$SCRIPT_DIR"
    
    if [ -f "version.py" ]; then
        # Get current version
        CURRENT_VERSION=$(python3 -c "import version; print(version.__version__)" 2>/dev/null || echo "1.0.0")
        
        # Extract version components
        IFS='.' read -r major minor patch <<< "$CURRENT_VERSION"
        
        # Increment patch version
        patch=$((patch + 1))
        NEW_VERSION="$major.$minor.$patch"
        
        # Update version file
        sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" version.py
        sed -i "s/__build_date__ = \".*\"/__build_date__ = \"$(date +%Y-%m-%d)\"/" version.py
        
        log_message "Version updated from $CURRENT_VERSION to $NEW_VERSION"
        return 0
    else
        log_message "Version file not found, skipping version update"
        return 1
    fi
}

# Function to apply updates
apply_updates() {
    cd "$SCRIPT_DIR"
    
    log_message "Applying updates..."
    
    # Backup current version
    BACKUP_DIR="/tmp/kiosk-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r . "$BACKUP_DIR/" 2>/dev/null || true
    log_message "Backup created at $BACKUP_DIR"
    
    # Pull updates
    if git pull origin main; then
        log_message "Updates applied successfully"
        
        # Update version number
        update_version
        
        # Make scripts executable
        chmod +x start_kiosk.sh
        chmod +x install_rpi.sh
        chmod +x update_check.sh
        
        # Update Python dependencies if requirements.txt changed
        if git diff HEAD~1 HEAD --name-only | grep -q "requirements.txt"; then
            log_message "Requirements.txt changed, updating dependencies..."
            if [ -d ".venv" ]; then
                .venv/bin/pip install -r requirements.txt
                log_message "Dependencies updated"
            fi
        fi
        
        return 0
    else
        log_message "Failed to apply updates"
        return 1
    fi
}

# Main function
main() {
    # Check if update checking is enabled
    if [ "$AUTO_UPDATE_CHECK" != "true" ]; then
        echo "Auto-update checking is disabled"
        exit 0
    fi
    
    # Check if we're on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        echo "Update check is only available on Raspberry Pi"
        exit 0
    fi
    
    log_message "Starting update check..."
    
    # Check internet connectivity
    if ! check_internet; then
        log_message "No internet connection. Skipping update check."
        exit 0
    fi
    
    # Check for updates
    if check_for_updates; then
        log_message "Updates found!"
        
        # Determine if we should apply updates automatically
        if [ "$AUTO_UPDATE_APPLY" = "true" ] || [ ! -t 0 ]; then
            # Apply updates automatically
            log_message "Auto-applying updates..."
            if apply_updates; then
                log_message "Automatic update completed successfully"
                # Create a flag file to indicate restart is needed
                touch /tmp/kiosk-restart-needed
                echo "Updates applied automatically. Application will restart with new version."
            else
                log_message "Automatic update failed"
                echo "Automatic update failed. Check logs at $UPDATE_LOG"
            fi
        else
            # Prompt user for updates
            echo "Updates are available for Office Kiosk Browser!"
            echo "Would you like to update now? (y/N): "
            read -r RESPONSE
            
            if [[ "$RESPONSE" =~ ^[Yy]$ ]]; then
                if apply_updates; then
                    echo "Update completed successfully!"
                    echo "The application will restart with the new version."
                    log_message "Interactive update completed successfully"
                    touch /tmp/kiosk-restart-needed
                else
                    echo "Update failed. Check logs at $UPDATE_LOG"
                    log_message "Interactive update failed"
                fi
            else
                echo "Update skipped by user"
                log_message "Update skipped by user"
            fi
        fi
    fi
    
    log_message "Update check completed"
}

# Run main function
main "$@"
