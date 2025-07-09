#!/bin/bash
# Trace Office Kiosk Browser autostart sources
# This script helps identify exactly which autostart method is launching multiple instances

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🔍 Office Kiosk Browser Autostart Tracer"
echo "========================================"
echo

# Function to check if a file contains autostart entries
check_file_for_autostart() {
    local file="$1"
    local description="$2"
    
    if [[ -f "$file" ]] && grep -q "office_kiosk\|kiosk_browser" "$file" 2>/dev/null; then
        warning "FOUND in $description: $file"
        echo "  Lines:"
        grep -n "office_kiosk\|kiosk_browser" "$file" 2>/dev/null | sed 's/^/    /'
        echo
        return 0
    fi
    return 1
}

# Function to check systemd service
check_systemd_service() {
    local service="$1"
    local scope="$2"  # "user" or "system"
    
    if command -v systemctl >/dev/null; then
        if [[ "$scope" == "user" ]]; then
            if systemctl --user is-enabled "$service" >/dev/null 2>&1; then
                warning "FOUND systemd USER service: $service"
                if systemctl --user is-active "$service" >/dev/null 2>&1; then
                    error "  Status: ACTIVE (currently running)"
                else
                    log "  Status: enabled but not active"
                fi
                
                # Show service file location
                local service_file="$HOME/.config/systemd/user/$service"
                if [[ -f "$service_file" ]]; then
                    echo "  File: $service_file"
                fi
                echo
                return 0
            fi
        else
            if systemctl is-enabled "$service" >/dev/null 2>&1; then
                warning "FOUND systemd SYSTEM service: $service"
                if systemctl is-active "$service" >/dev/null 2>&1; then
                    error "  Status: ACTIVE (currently running)"
                else
                    log "  Status: enabled but not active"
                fi
                
                # Show service file location
                local service_file="/etc/systemd/system/$service"
                if [[ -f "$service_file" ]]; then
                    echo "  File: $service_file"
                fi
                echo
                return 0
            fi
        fi
    fi
    return 1
}

# Main tracing
echo "🔎 Scanning ALL possible autostart locations..."
echo "=============================================="
echo

FOUND_SOURCES=0

# Desktop autostart
if [[ -f "$HOME/.config/autostart/office-kiosk-browser.desktop" ]]; then
    warning "FOUND desktop autostart: $HOME/.config/autostart/office-kiosk-browser.desktop"
    echo "  This is the PRIMARY autostart method (good if only one)"
    echo
    ((FOUND_SOURCES++))
fi

# Other desktop files
OTHER_DESKTOP=$(find "$HOME/.config/autostart/" -name "*kiosk*" -o -name "*office*" 2>/dev/null | grep -v "office-kiosk-browser.desktop" || true)
if [[ -n "$OTHER_DESKTOP" ]]; then
    warning "FOUND other desktop autostart files:"
    echo "$OTHER_DESKTOP" | while read -r file; do
        echo "  $file"
        ((FOUND_SOURCES++))
    done
    echo
fi

# Shell initialization files
for file_info in \
    "$HOME/.bashrc:Bash shell startup" \
    "$HOME/.profile:Shell profile" \
    "$HOME/.bash_profile:Bash profile" \
    "$HOME/.xinitrc:X11 initialization" \
    "$HOME/.xsessionrc:X session startup"; do
    
    file="${file_info%:*}"
    desc="${file_info#*:}"
    if check_file_for_autostart "$file" "$desc"; then
        ((FOUND_SOURCES++))
    fi
done

# System files
if check_file_for_autostart "/etc/rc.local" "System startup script"; then
    ((FOUND_SOURCES++))
fi

# Crontab
if crontab -l 2>/dev/null | grep -q "office_kiosk\|kiosk_browser"; then
    warning "FOUND in crontab:"
    crontab -l 2>/dev/null | grep -n "office_kiosk\|kiosk_browser" | sed 's/^/  /'
    echo
    ((FOUND_SOURCES++))
fi

# Systemd services
for service in "office-kiosk-browser.service" "kiosk-browser.service" "kiosk_browser.service" "office-kiosk.service"; do
    if check_systemd_service "$service" "user"; then
        ((FOUND_SOURCES++))
    fi
    if check_systemd_service "$service" "system"; then
        ((FOUND_SOURCES++))
    fi
done

echo "📊 SUMMARY:"
echo "==========="
if [[ $FOUND_SOURCES -eq 0 ]]; then
    success "✅ No autostart sources found"
    log "This means autostart is disabled or the app is being started manually"
elif [[ $FOUND_SOURCES -eq 1 ]]; then
    success "✅ Exactly 1 autostart source found (this is correct)"
    log "This should work properly without multiple instances"
else
    error "❌ MULTIPLE autostart sources found: $FOUND_SOURCES"
    error "This is why you're getting multiple instances!"
    echo
    echo "🔧 TO FIX:"
    echo "1. Run: ./install/manage_autostart.sh disable"
    echo "2. Run: ./install/manage_autostart.sh enable"
    echo "3. Reboot and test"
fi

echo
echo "🔍 Current running instances:"
if pgrep -f "kiosk_browser.py" >/dev/null; then
    RUNNING_COUNT=$(pgrep -f "kiosk_browser.py" | wc -l)
    if [[ $RUNNING_COUNT -gt 1 ]]; then
        error "❌ $RUNNING_COUNT instances currently running"
        echo "PIDs: $(pgrep -f 'kiosk_browser.py' | tr '\n' ' ')"
    else
        success "✅ 1 instance currently running"
        echo "PID: $(pgrep -f 'kiosk_browser.py')"
    fi
else
    log "❌ No instances currently running"
fi

echo
echo "💡 Next steps:"
if [[ $FOUND_SOURCES -gt 1 ]]; then
    echo "1. ./install/manage_autostart.sh stop     # Stop all running instances"
    echo "2. ./install/manage_autostart.sh disable  # Remove ALL autostart methods"
    echo "3. ./install/manage_autostart.sh enable   # Set up only ONE method"
    echo "4. ./install/manage_autostart.sh status   # Verify the fix"
    echo "5. Reboot to test"
else
    echo "Run './install/manage_autostart.sh debug' for more detailed process information"
fi
