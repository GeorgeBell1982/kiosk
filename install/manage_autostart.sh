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
        else
            success "✅ App currently running (PID: $RUNNING_PIDS)"
        fi
    else
        log "❌ App not currently running"
    fi
    echo
    
    # Check desktop autostart
    DESKTOP_AUTOSTART="$HOME/.config/autostart/office-kiosk-browser.desktop"
    if [[ -f "$DESKTOP_AUTOSTART" ]]; then
        success "✅ Desktop autostart: ENABLED"
    else
        warning "❌ Desktop autostart: DISABLED"
    fi
    
    # Check systemd user service
    if command -v systemctl >/dev/null; then
        if systemctl --user is-enabled office-kiosk-browser.service >/dev/null 2>&1; then
            success "✅ Systemd user service: ENABLED"
        else
            warning "❌ Systemd user service: DISABLED"
        fi
    else
        warning "❌ Systemd: NOT AVAILABLE"
    fi
    
    # Check .bashrc
    if grep -q "office_kiosk" "$HOME/.bashrc" 2>/dev/null; then
        success "✅ Bashrc autostart: ENABLED"
    else
        warning "❌ Bashrc autostart: DISABLED"
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
    log "Disabling autostart..."
    
    # Remove desktop autostart
    DESKTOP_AUTOSTART="$HOME/.config/autostart/office-kiosk-browser.desktop"
    if [[ -f "$DESKTOP_AUTOSTART" ]]; then
        rm "$DESKTOP_AUTOSTART"
        success "Removed desktop autostart"
    fi
    
    # Disable systemd user service
    if command -v systemctl >/dev/null; then
        if systemctl --user is-enabled office-kiosk-browser.service >/dev/null 2>&1; then
            systemctl --user disable office-kiosk-browser.service
            systemctl --user stop office-kiosk-browser.service 2>/dev/null || true
            success "Disabled systemd user service"
        fi
    fi
    
    # Remove from .bashrc
    if grep -q "office_kiosk" "$HOME/.bashrc" 2>/dev/null; then
        # Create a backup
        cp "$HOME/.bashrc" "$HOME/.bashrc.backup.$(date +%Y%m%d_%H%M%S)"
        # Remove the autostart section
        sed -i '/# Auto-start Office Kiosk Browser/,/^fi$/d' "$HOME/.bashrc"
        success "Removed .bashrc autostart (backup created)"
    fi
    
    success "Autostart disabled"
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

# Show usage
usage() {
    echo "Usage: $0 [enable|disable|status|stop|restart]"
    echo
    echo "Commands:"
    echo "  enable   - Enable autostart (setup desktop autostart method)"
    echo "  disable  - Disable autostart (remove all autostart methods)"
    echo "  status   - Show current autostart status and running instances"
    echo "  stop     - Stop all running instances of the app"
    echo "  restart  - Stop all instances and start a new one"
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
