#!/bin/bash
# Quick PyQt6 Installation Script for Raspberry Pi
# Tries multiple installation methods in order of preference

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test if PyQt6 is working
test_pyqt6() {
    python3 -c "
import sys
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    print('PyQt6 core: OK')
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        print('PyQt6 WebEngine: OK')
        sys.exit(0)
    except ImportError:
        print('PyQt6 WebEngine: NOT AVAILABLE')
        sys.exit(1)
except ImportError as e:
    print(f'PyQt6: FAILED - {e}')
    sys.exit(2)
" 2>/dev/null
    return $?
}

# Method 1: System packages (fastest)
try_system_packages() {
    log "Method 1: Trying system packages..."
    
    sudo apt update -qq
    
    if sudo apt install -y python3-pyqt6 python3-pyqt6.qtwebengine 2>/dev/null; then
        success "System packages installed"
        if test_pyqt6; then
            success "PyQt6 working with system packages!"
            return 0
        else
            warning "System packages installed but not working properly"
        fi
    else
        warning "System packages not available"
    fi
    
    return 1
}

# Method 2: Pip with piwheels (medium speed)
try_pip_piwheels() {
    log "Method 2: Trying pip with piwheels..."
    
    # Use piwheels index for pre-compiled ARM packages
    if pip3 install --extra-index-url https://www.piwheels.org/simple/ PyQt6 PyQt6-WebEngine; then
        success "Piwheels packages installed"
        if test_pyqt6; then
            success "PyQt6 working with piwheels!"
            return 0
        else
            warning "Piwheels packages installed but not working properly"
        fi
    else
        warning "Piwheels installation failed"
    fi
    
    return 1
}

# Method 3: Regular pip (slower)
try_regular_pip() {
    log "Method 3: Trying regular pip..."
    
    if pip3 install PyQt6 PyQt6-WebEngine; then
        success "Regular pip packages installed"
        if test_pyqt6; then
            success "PyQt6 working with regular pip!"
            return 0
        else
            warning "Regular pip packages installed but not working properly"
        fi
    else
        warning "Regular pip installation failed"
    fi
    
    return 1
}

# Method 4: Build from source (slowest)
try_build_from_source() {
    log "Method 4: Building from source..."
    warning "This will take several hours!"
    
    read -p "Continue with build from source? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Run the full build script
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        bash "$SCRIPT_DIR/build_pyqt6_rpi.sh"
        return $?
    else
        log "Build from source cancelled"
        return 1
    fi
}

# Main function
main() {
    log "PyQt6 Quick Install for Raspberry Pi"
    log "===================================="
    
    # Check if running on Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        error "This script is for Raspberry Pi only!"
        exit 1
    fi
    
    PI_MODEL=$(cat /proc/cpuinfo | grep "Model" | head -1 | cut -d':' -f2 | xargs)
    log "Detected: $PI_MODEL"
    
    # Check if PyQt6 is already working
    log "Checking existing PyQt6 installation..."
    if test_pyqt6; then
        success "PyQt6 with WebEngine is already installed and working!"
        success "You can run: python3 kiosk_browser.py"
        exit 0
    fi
    
    # Try installation methods in order
    log "PyQt6 not found or not working. Trying installation methods..."
    
    if try_system_packages; then
        success "Installation successful via system packages!"
    elif try_pip_piwheels; then
        success "Installation successful via piwheels!"
    elif try_regular_pip; then
        success "Installation successful via regular pip!"
    elif try_build_from_source; then
        success "Installation successful via build from source!"
    else
        error "All installation methods failed!"
        error "You may need to:"
        error "1. Update your Raspberry Pi OS to a newer version"
        error "2. Check your internet connection"
        error "3. Try manual installation"
        exit 1
    fi
    
    # Final test
    log "Final verification..."
    if test_pyqt6; then
        success "🎉 PyQt6 installation complete and verified!"
        success "You can now run: python3 test_qt_version.py"
        success "And then: python3 kiosk_browser.py"
    else
        error "Installation completed but final test failed"
        exit 1
    fi
}

main "$@"
