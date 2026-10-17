#!/bin/bash
# Auto-update script for Office Kiosk Browser
# Checks for updates from GitHub repository and prompts for update

REPO_URL="https://github.com/GeorgeBell1982/kiosk.git"
UPDATE_LOG="${XDG_STATE_HOME:-$HOME/.local/state}/office-kiosk/update.log"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/update_config.conf"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Run repository operations from the project root
cd "$PROJECT_DIR" || exit 1

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
    local message="$(date '+%Y-%m-%d %H:%M:%S') - $1"
    printf '%s\n' "$message"
    if ! { mkdir -p "$(dirname "$UPDATE_LOG")" && printf '%s\n' "$message" >> "$UPDATE_LOG"; }; then
        printf 'Could not write update log: %s\n' "$UPDATE_LOG" >&2
    fi
    return 0
}

# Function to check for updates
check_for_updates() {
    cd "$PROJECT_DIR" || exit 1
    
    log_message "Checking for updates..."
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        log_message "Not a git repository. Skipping update check."
        return 1
    fi
    
    # Fetch latest changes
    if ! GIT_TERMINAL_PROMPT=0 timeout --kill-after=5 "$UPDATE_TIMEOUT" git fetch origin main; then
        log_message "Failed to fetch updates from remote repository"
        return 2
    fi

    # Check if we're behind
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)
    
    if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
        log_message "Already up to date"
        return 1
    elif git merge-base --is-ancestor "$LOCAL_COMMIT" "$REMOTE_COMMIT"; then
        log_message "Updates available! Local: $LOCAL_COMMIT, Remote: $REMOTE_COMMIT"
        return 0
    else
        log_message "Local branch is ahead of or diverged from origin/main; skipping automatic update"
        return 1
    fi
}

# Function to apply updates
apply_updates() {
    cd "$PROJECT_DIR" || exit 1
    
    log_message "Applying updates..."
    
    # Backup current version
    BACKUP_DIR="/tmp/kiosk-backup-$(date +%Y%m%d-%H%M%S)"
    if ! mkdir -p "$BACKUP_DIR" || ! cp -r . "$BACKUP_DIR/"; then
        log_message "Backup failed; update was not applied"
        return 1
    fi
    log_message "Backup created at $BACKUP_DIR"
    
    PREVIOUS_COMMIT=$(git rev-parse HEAD) || return 1

    # Apply the exact fetched commit without another network request.
    if git merge --ff-only "$REMOTE_COMMIT"; then
        log_message "Updates applied successfully"
        
        # Make scripts executable
        chmod +x scripts/*.sh install/*.sh
        
        # Check the entire update range, including changes before the final commit.
        if git diff "$PREVIOUS_COMMIT" HEAD --name-only | grep -Eq '^requirements(-rpi)?\.txt$'; then
            if [ -d ".venv" ]; then
                requirements_file="requirements.txt"
                if [ -f "requirements-rpi.txt" ]; then
                    requirements_file="requirements-rpi.txt"
                fi
                log_message "Updating dependencies from $requirements_file..."
                if ! .venv/bin/python -m pip install -r "$requirements_file"; then
                    log_message "Dependency installation failed. Restore $BACKUP_DIR or retry pip installation manually."
                    return 1
                fi
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
    
    if [[ ! "$UPDATE_TIMEOUT" =~ ^[1-9][0-9]*$ ]]; then
        log_message "UPDATE_TIMEOUT must be a positive integer"
        exit 1
    fi

    # Check for updates
    if check_for_updates; then
        log_message "Updates found! Starting automatic update process..."
        
        # Determine if we should apply updates automatically
        if [ "$AUTO_UPDATE_APPLY" = "true" ]; then
            # Apply updates automatically
            log_message "Auto-applying updates (AUTO_UPDATE_APPLY=true, no user interaction)..."
            echo "Applying updates automatically..."
            if apply_updates; then
                log_message "Automatic update completed successfully"
                # Create a flag file to indicate restart is needed
                touch /tmp/kiosk-restart-needed
                echo "Updates applied automatically. Application will restart with new version."
                # Signal that updates were applied (for parent process detection)
                echo "UPDATES_APPLIED_AUTOMATICALLY"
                exit 0
            else
                log_message "Automatic update failed"
                echo "Automatic update failed. Check logs at $UPDATE_LOG"
                exit 1
            fi
        elif [ ! -t 0 ]; then
            echo "Updates are available; automatic application is disabled."
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
    else
        status=$?
        if [ "$status" -gt 1 ]; then
            exit 1
        fi
    fi

    log_message "Update check completed"
}

# Run main function
main "$@"
