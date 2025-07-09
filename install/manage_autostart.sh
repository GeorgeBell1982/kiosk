#!/bin/bash
# Manage Office Kiosk Browser autostart

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check autostart status
check_autostart_status() {
    echo "Office Kiosk Browser Autostart Status"
    echo "===================================="
    echo
    
    # Check if app is currently running
    if pgrep -f "kiosk_browser.py" >/dev/null; then
        RUNNING_PIDS=$(pgrep -f "kiosk_browser.py" | tr '\n' ' ')
        NUM_INSTANCES=$(echo $RUNNING_PIDS | wc -w)
        if [ $NUM_INSTANCES -gt 1 ]; then
            warning "⚠️  Multiple instances running (PIDs: $RUNNING_PIDS)"
            warning "   This causes conflicts - run './install/manage_autostart.sh stop' to fix"
            echo "   Let's find where they're starting from..."
        else
            success "✅ App currently running (PID: $RUNNING_PIDS)"
        fi
    else
        log "❌ App not currently running"
    fi
    echo
    
    echo "🔍 Checking ALL possible autostart locations:"
    echo "=============================================="
    
    # Check desktop autostart
    DESKTOP_AUTOSTART="$HOME/.config/autostart/office-kiosk-browser.desktop"
    if [[ -f "$DESKTOP_AUTOSTART" ]]; then
        warning "⚠️  Desktop autostart: ENABLED at $DESKTOP_AUTOSTART"
    else
        success "✅ Desktop autostart: DISABLED"
    fi
    
    # Check for any other desktop files in autostart
    OTHER_DESKTOP_FILES=$(find "$HOME/.config/autostart/" -name "*kiosk*" -o -name "*office*" 2>/dev/null || true)
    if [[ -n "$OTHER_DESKTOP_FILES" ]]; then
        warning "⚠️  Other autostart files found:"
        echo "$OTHER_DESKTOP_FILES" | while read -r file; do
            warning "     $file"
        done
    fi
    
    # Check systemd user service
    if command -v systemctl >/dev/null; then
        if systemctl --user is-enabled office-kiosk-browser.service >/dev/null 2>&1; then
            warning "⚠️  Systemd user service: ENABLED"
        else
            success "✅ Systemd user service: DISABLED"
        fi
        
        # Check if service is running
        if systemctl --user is-active office-kiosk-browser.service >/dev/null 2>&1; then
            warning "⚠️  Systemd service is currently ACTIVE"
        fi
    else
        success "✅ Systemd: NOT AVAILABLE"
    fi
    
    # Check .bashrc
    if grep -q "office_kiosk\|kiosk_browser" "$HOME/.bashrc" 2>/dev/null; then
        warning "⚠️  Bashrc autostart: ENABLED"
        echo "     Lines found:"
        grep -n "office_kiosk\|kiosk_browser" "$HOME/.bashrc" 2>/dev/null | sed 's/^/     /'
    else
        success "✅ Bashrc autostart: DISABLED"
    fi
    
    # Check .profile
    if grep -q "office_kiosk\|kiosk_browser" "$HOME/.profile" 2>/dev/null; then
        warning "⚠️  .profile autostart: ENABLED"
        echo "     Lines found:"
        grep -n "office_kiosk\|kiosk_browser" "$HOME/.profile" 2>/dev/null | sed 's/^/     /'
    else
        success "✅ .profile autostart: DISABLED"
    fi
    
    # Check /etc/rc.local
    if [[ -f "/etc/rc.local" ]] && grep -q "office_kiosk\|kiosk_browser" "/etc/rc.local" 2>/dev/null; then
        warning "⚠️  /etc/rc.local autostart: ENABLED"
        echo "     Lines found:"
        grep -n "office_kiosk\|kiosk_browser" "/etc/rc.local" 2>/dev/null | sed 's/^/     /'
    else
        success "✅ /etc/rc.local autostart: DISABLED"
    fi
    
    # Check crontab
    CRON_CHECK=$(crontab -l 2>/dev/null | grep -i "office_kiosk\|kiosk_browser" || true)
    if [[ -n "$CRON_CHECK" ]]; then
        warning "⚠️  Crontab autostart: ENABLED"
        echo "     Lines found:"
        echo "$CRON_CHECK" | sed 's/^/     /'
    else
        success "✅ Crontab autostart: DISABLED"
    fi
    
    # Check .xinitrc
    if [[ -f "$HOME/.xinitrc" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.xinitrc" 2>/dev/null; then
        warning "⚠️  .xinitrc autostart: ENABLED"
        echo "     Lines found:"
        grep -n "office_kiosk\|kiosk_browser" "$HOME/.xinitrc" 2>/dev/null | sed 's/^/     /'
    else
        success "✅ .xinitrc autostart: DISABLED"
    fi
    
    # Check .xsessionrc
    if [[ -f "$HOME/.xsessionrc" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.xsessionrc" 2>/dev/null; then
        warning "⚠️  .xsessionrc autostart: ENABLED"
        echo "     Lines found:"
        grep -n "office_kiosk\|kiosk_browser" "$HOME/.xsessionrc" 2>/dev/null | sed 's/^/     /'
    else
        success "✅ .xsessionrc autostart: DISABLED"
    fi
    
    # Check .bash_profile
    if [[ -f "$HOME/.bash_profile" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.bash_profile" 2>/dev/null; then
        warning "⚠️  .bash_profile autostart: ENABLED"
        echo "     Lines found:"
        grep -n "office_kiosk\|kiosk_browser" "$HOME/.bash_profile" 2>/dev/null | sed 's/^/     /'
    else
        success "✅ .bash_profile autostart: DISABLED"
    fi
    
    # Check old systemd service names and locations
    for service_name in "kiosk-browser.service" "kiosk_browser.service" "office-kiosk.service"; do
        # Check system-wide service
        if [[ -f "/etc/systemd/system/$service_name" ]]; then
            warning "⚠️  Old system-wide service found: /etc/systemd/system/$service_name"
            if systemctl is-enabled "$service_name" >/dev/null 2>&1; then
                warning "     And it's ENABLED!"
            fi
        fi
        
        # Check user service
        if [[ -f "$HOME/.config/systemd/user/$service_name" ]]; then
            warning "⚠️  Old user service found: $HOME/.config/systemd/user/$service_name"
            if systemctl --user is-enabled "$service_name" >/dev/null 2>&1; then
                warning "     And it's ENABLED!"
            fi
        fi
    done
    
    # Check for any systemd service that might be running our app
    if command -v systemctl >/dev/null; then
        RUNNING_SERVICES=$(systemctl --user list-units --state=active | grep -i "kiosk\|office" || true)
        if [[ -n "$RUNNING_SERVICES" ]]; then
            warning "⚠️  Active systemd services found:"
            echo "$RUNNING_SERVICES" | sed 's/^/     /'
        fi
        
        SYSTEM_RUNNING_SERVICES=$(systemctl list-units --state=active | grep -i "kiosk\|office" || true)
        if [[ -n "$SYSTEM_RUNNING_SERVICES" ]]; then
            warning "⚠️  Active system-wide services found:"
            echo "$SYSTEM_RUNNING_SERVICES" | sed 's/^/     /'
        fi
    fi
    
    echo
    echo "📊 Summary:"
    ENABLED_COUNT=0
    if [[ -f "$DESKTOP_AUTOSTART" ]]; then ((ENABLED_COUNT++)); fi
    if command -v systemctl >/dev/null && systemctl --user is-enabled office-kiosk-browser.service >/dev/null 2>&1; then ((ENABLED_COUNT++)); fi
    if grep -q "office_kiosk\|kiosk_browser" "$HOME/.bashrc" 2>/dev/null; then ((ENABLED_COUNT++)); fi
    if grep -q "office_kiosk\|kiosk_browser" "$HOME/.profile" 2>/dev/null; then ((ENABLED_COUNT++)); fi
    if [[ -f "$HOME/.xinitrc" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.xinitrc" 2>/dev/null; then ((ENABLED_COUNT++)); fi
    if [[ -f "$HOME/.xsessionrc" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.xsessionrc" 2>/dev/null; then ((ENABLED_COUNT++)); fi
    if [[ -f "$HOME/.bash_profile" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.bash_profile" 2>/dev/null; then ((ENABLED_COUNT++)); fi
    if [[ -f "/etc/rc.local" ]] && grep -q "office_kiosk\|kiosk_browser" "/etc/rc.local" 2>/dev/null; then ((ENABLED_COUNT++)); fi
    if crontab -l 2>/dev/null | grep -q "office_kiosk\|kiosk_browser"; then ((ENABLED_COUNT++)); fi
    
    # Check for old services
    for service_name in "kiosk-browser.service" "kiosk_browser.service" "office-kiosk.service"; do
        if [[ -f "/etc/systemd/system/$service_name" ]] && systemctl is-enabled "$service_name" >/dev/null 2>&1; then ((ENABLED_COUNT++)); fi
        if [[ -f "$HOME/.config/systemd/user/$service_name" ]] && systemctl --user is-enabled "$service_name" >/dev/null 2>&1; then ((ENABLED_COUNT++)); fi
    done
    
    if [[ $ENABLED_COUNT -gt 1 ]]; then
        error "❌ PROBLEM: $ENABLED_COUNT autostart methods enabled - this causes multiple instances!"
        warning "   Run './install/manage_autostart.sh disable' to remove ALL autostart methods"
        warning "   Then run './install/manage_autostart.sh enable' to set up only one method"
    elif [[ $ENABLED_COUNT -eq 1 ]]; then
        success "✅ Good: Only 1 autostart method enabled"
    else
        log "ℹ️  No autostart methods enabled"
    fi
    
    echo
}

# Enable autostart
enable_autostart() {
    log "Enabling autostart..."
    chmod +x "$SCRIPT_DIR/setup_autostart.sh"
    "$SCRIPT_DIR/setup_autostart.sh"
}

# Disable autostart
disable_autostart() {
    log "Disabling ALL autostart methods..."
    
    # Remove desktop autostart
    DESKTOP_AUTOSTART="$HOME/.config/autostart/office-kiosk-browser.desktop"
    if [[ -f "$DESKTOP_AUTOSTART" ]]; then
        rm "$DESKTOP_AUTOSTART"
        success "Removed desktop autostart"
    fi
    
    # Remove any other desktop files in autostart
    OTHER_DESKTOP_FILES=$(find "$HOME/.config/autostart/" -name "*kiosk*" -o -name "*office*" 2>/dev/null || true)
    if [[ -n "$OTHER_DESKTOP_FILES" ]]; then
        echo "$OTHER_DESKTOP_FILES" | while read -r file; do
            if [[ -f "$file" ]]; then
                rm "$file"
                success "Removed $file"
            fi
        done
    fi
    
    # Disable systemd user service
    if command -v systemctl >/dev/null; then
        if systemctl --user is-enabled office-kiosk-browser.service >/dev/null 2>&1; then
            systemctl --user disable office-kiosk-browser.service
            systemctl --user stop office-kiosk-browser.service 2>/dev/null || true
            success "Disabled systemd user service"
        fi
        
        # Remove user service file if it exists
        USER_SERVICE_FILE="$HOME/.config/systemd/user/office-kiosk-browser.service"
        if [[ -f "$USER_SERVICE_FILE" ]]; then
            rm "$USER_SERVICE_FILE"
            systemctl --user daemon-reload
            success "Removed user service file"
        fi
    fi
    
    # Remove from .bashrc
    if grep -q "office_kiosk\|kiosk_browser" "$HOME/.bashrc" 2>/dev/null; then
        # Create a backup
        cp "$HOME/.bashrc" "$HOME/.bashrc.backup.$(date +%Y%m%d_%H%M%S)"
        # Remove the autostart section
        sed -i '/# Auto-start Office Kiosk Browser/,/^fi$/d' "$HOME/.bashrc"
        # Also remove any other kiosk-related lines
        sed -i '/office_kiosk\|kiosk_browser/d' "$HOME/.bashrc"
        success "Removed .bashrc autostart (backup created)"
    fi
    
    # Remove from .profile
    if grep -q "office_kiosk\|kiosk_browser" "$HOME/.profile" 2>/dev/null; then
        cp "$HOME/.profile" "$HOME/.profile.backup.$(date +%Y%m%d_%H%M%S)"
        sed -i '/office_kiosk\|kiosk_browser/d' "$HOME/.profile"
        success "Removed .profile autostart (backup created)"
    fi
    
    # Remove from .xinitrc
    if [[ -f "$HOME/.xinitrc" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.xinitrc" 2>/dev/null; then
        cp "$HOME/.xinitrc" "$HOME/.xinitrc.backup.$(date +%Y%m%d_%H%M%S)"
        sed -i '/office_kiosk\|kiosk_browser/d' "$HOME/.xinitrc"
        success "Removed .xinitrc autostart (backup created)"
    fi
    
    # Remove from .xsessionrc
    if [[ -f "$HOME/.xsessionrc" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.xsessionrc" 2>/dev/null; then
        cp "$HOME/.xsessionrc" "$HOME/.xsessionrc.backup.$(date +%Y%m%d_%H%M%S)"
        sed -i '/office_kiosk\|kiosk_browser/d' "$HOME/.xsessionrc"
        success "Removed .xsessionrc autostart (backup created)"
    fi
    
    # Remove from .bash_profile
    if [[ -f "$HOME/.bash_profile" ]] && grep -q "office_kiosk\|kiosk_browser" "$HOME/.bash_profile" 2>/dev/null; then
        cp "$HOME/.bash_profile" "$HOME/.bash_profile.backup.$(date +%Y%m%d_%H%M%S)"
        sed -i '/office_kiosk\|kiosk_browser/d' "$HOME/.bash_profile"
        success "Removed .bash_profile autostart (backup created)"
    fi
    
    # Check and warn about /etc/rc.local (needs sudo to remove)
    if [[ -f "/etc/rc.local" ]] && grep -q "office_kiosk\|kiosk_browser" "/etc/rc.local" 2>/dev/null; then
        warning "Found autostart in /etc/rc.local - requires manual removal with sudo:"
        warning "sudo nano /etc/rc.local"
        grep -n "office_kiosk\|kiosk_browser" "/etc/rc.local" 2>/dev/null | sed 's/^/  Remove line: /'
    fi
    
    # Remove from crontab
    CRON_CHECK=$(crontab -l 2>/dev/null | grep -v "office_kiosk\|kiosk_browser" || true)
    if crontab -l 2>/dev/null | grep -q "office_kiosk\|kiosk_browser"; then
        echo "$CRON_CHECK" | crontab -
        success "Removed crontab autostart"
    fi
    
    # Check old system-wide services
    for service_name in "kiosk-browser.service" "kiosk_browser.service" "office-kiosk.service"; do
        if [[ -f "/etc/systemd/system/$service_name" ]]; then
            warning "Found old system-wide service: /etc/systemd/system/$service_name"
            warning "Requires manual removal with sudo:"
            warning "  sudo systemctl disable $service_name"
            warning "  sudo systemctl stop $service_name"
            warning "  sudo rm /etc/systemd/system/$service_name"
            warning "  sudo systemctl daemon-reload"
        fi
        
        # Remove old user services
        if [[ -f "$HOME/.config/systemd/user/$service_name" ]]; then
            if systemctl --user is-enabled "$service_name" >/dev/null 2>&1; then
                systemctl --user disable "$service_name"
                systemctl --user stop "$service_name" 2>/dev/null || true
            fi
            rm "$HOME/.config/systemd/user/$service_name"
            systemctl --user daemon-reload
            success "Removed old user service: $service_name"
        fi
    done
    
    success "All autostart methods disabled"
}

# Stop running instances
stop_running_instances() {
    log "Stopping all running Office Kiosk Browser instances..."
    
    if pgrep -f "kiosk_browser.py" >/dev/null; then
        RUNNING_PIDS=$(pgrep -f "kiosk_browser.py")
        echo "  Found running instances: $RUNNING_PIDS"
        
        # Stop gracefully first
        pkill -f "kiosk_browser.py"
        sleep 2
        
        # Force kill if still running
        if pgrep -f "kiosk_browser.py" >/dev/null; then
            warning "  Some instances still running, force killing..."
            pkill -9 -f "kiosk_browser.py"
            sleep 1
        fi
        
        # Also clean up virtual keyboard processes
        pkill -f "wvkbd-mobintl" 2>/dev/null || true
        
        if pgrep -f "kiosk_browser.py" >/dev/null; then
            error "Failed to stop all instances"
            return 1
        else
            success "All instances stopped"
            return 0
        fi
    else
        log "No running instances found"
        return 0
    fi
}

# Debug running instances
debug_instances() {
    log "Debugging running instances..."
    echo
    
    echo "🔍 Checking for running processes:"
    echo "=================================="
    
    if pgrep -f "kiosk_browser.py" >/dev/null; then
        RUNNING_PIDS=$(pgrep -f "kiosk_browser.py")
        NUM_INSTANCES=$(echo $RUNNING_PIDS | wc -w)
        
        if [ $NUM_INSTANCES -gt 1 ]; then
            error "❌ MULTIPLE INSTANCES DETECTED ($NUM_INSTANCES instances)"
            echo "This is the source of your problem!"
        else
            success "✅ Single instance running (good)"
        fi
        
        echo
        echo "📋 Detailed process information:"
        for pid in $RUNNING_PIDS; do
            echo "  🔹 PID: $pid"
            if [[ -f "/proc/$pid/cmdline" ]]; then
                echo "    Command: $(cat /proc/$pid/cmdline | tr '\0' ' ')"
            fi
            if [[ -f "/proc/$pid/stat" ]]; then
                PPID=$(awk '{print $4}' /proc/$pid/stat)
                echo "    Parent PID: $PPID"
                if [[ -f "/proc/$PPID/cmdline" ]]; then
                    PARENT_CMD=$(cat /proc/$PPID/cmdline | tr '\0' ' ')
                    echo "    Parent Command: $PARENT_CMD"
                    
                    # Try to identify the autostart source
                    case "$PARENT_CMD" in
                        *systemd*)
                            warning "    ⚠️  Started by: SYSTEMD SERVICE"
                            ;;
                        *bash*|*sh*)
                            warning "    ⚠️  Started by: SHELL SCRIPT (check .bashrc, .profile, etc.)"
                            ;;
                        *cron*)
                            warning "    ⚠️  Started by: CRON JOB"
                            ;;
                        *desktop*)
                            warning "    ⚠️  Started by: DESKTOP AUTOSTART"
                            ;;
                        *)
                            log "    ℹ️  Started by: $PARENT_CMD"
                            ;;
                    esac
                fi
            fi
            
            # Check process start time
            if [[ -f "/proc/$pid/stat" ]]; then
                START_TIME=$(awk '{print $22}' /proc/$pid/stat)
                BOOT_TIME=$(awk '/btime/ {print $2}' /proc/stat)
                START_SECONDS=$((BOOT_TIME + START_TIME / 100))
                START_DATE=$(date -d "@$START_SECONDS" 2>/dev/null || echo "unknown")
                echo "    Started: $START_DATE"
            fi
            echo
        done
        
        if command -v pstree >/dev/null; then
            echo "🌳 Process tree:"
            for pid in $RUNNING_PIDS; do
                echo "  Instance $pid:"
                pstree -p $pid 2>/dev/null || echo "    Unable to show tree"
            done
        fi
        
        echo
        echo "📊 Full process list:"
        ps aux | head -1
        ps aux | grep "kiosk_browser.py" | grep -v grep
        
    else
        log "❌ No running instances found"
        echo "  This might indicate the app crashed or was stopped."
    fi
    
    echo
    echo "🖥️  Virtual keyboard processes:"
    if pgrep -f "wvkbd" >/dev/null; then
        ps aux | grep "wvkbd" | grep -v grep
    else
        log "  No virtual keyboard processes running"
    fi
    
    echo
    echo "🔧 System information:"
    echo "  Display server: ${XDG_SESSION_TYPE:-unknown}"
    echo "  Desktop environment: ${XDG_CURRENT_DESKTOP:-unknown}"
    echo "  Session: ${XDG_SESSION_DESKTOP:-unknown}"
    
    if command -v loginctl >/dev/null; then
        echo "  Active sessions:"
        loginctl list-sessions 2>/dev/null | head -5 || echo "    Unable to list sessions"
    fi
    
    echo
    echo "💡 Recommendations:"
    if [[ $NUM_INSTANCES -gt 1 ]]; then
        error "  1. Stop all instances: ./install/manage_autostart.sh stop"
        error "  2. Disable all autostart: ./install/manage_autostart.sh disable"
        error "  3. Enable only one method: ./install/manage_autostart.sh enable"
        error "  4. Check status: ./install/manage_autostart.sh status"
    else
        success "  Process state looks normal. If having issues, check the status command."
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [enable|disable|status|stop|restart|debug]"
    echo
    echo "Commands:"
    echo "  enable   - Enable autostart (setup desktop autostart method)"
    echo "  disable  - Disable ALL autostart methods (comprehensive cleanup)"
    echo "  status   - Show current autostart status and running instances"
    echo "  stop     - Stop all running instances of the app"
    echo "  restart  - Stop all instances and start a new one"
    echo "  debug    - Debug running instances and their parent processes"
    echo "  trace    - Quick trace of all autostart sources (use trace_autostart.sh)"
    echo
    echo "If no command is provided, status will be shown."
}

# Main function
main() {
    case "${1:-status}" in
        "enable")
            enable_autostart
            echo
            check_autostart_status
            ;;
        "disable")
            disable_autostart
            echo
            check_autostart_status
            ;;
        "status")
            check_autostart_status
            ;;
        "stop")
            stop_running_instances
            ;;
        "restart")
            stop_running_instances
            echo
            log "Starting new instance..."
            cd "$PROJECT_DIR"
            python3 kiosk_browser.py --fullscreen &
            sleep 2
            check_autostart_status
            ;;
        "debug")
            debug_instances
            ;;
        "trace")
            log "Running autostart tracer..."
            chmod +x "$SCRIPT_DIR/trace_autostart.sh" 2>/dev/null || true
            "$SCRIPT_DIR/trace_autostart.sh"
            ;;
        "help"|"-h"|"--help")
            usage
            ;;
        *)
            error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"
