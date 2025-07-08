#!/bin/bash
# Quick PyQt6 Installation Script for Raspberry Pi (Bookworm+)
# Fully automated Qt6 installation with no Qt5 references
# Optimized for Raspberry Pi OS Bookworm and newer versions

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

# Test if PyQt6 is working with all required modules
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
        try:
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtSvgWidgets import QSvgWidget
            print('PyQt6 SVG: OK')
            sys.exit(0)
        except ImportError:
            print('PyQt6 SVG: NOT AVAILABLE')
            sys.exit(1)
    except ImportError:
        print('PyQt6 WebEngine: NOT AVAILABLE')
        sys.exit(1)
except ImportError as e:
    print(f'PyQt6: FAILED - {e}')
    sys.exit(2)
" 2>/dev/null
    return $?
}

# Method 1: System packages (fastest and preferred for Bookworm)
try_system_packages() {
    log "Method 1: Installing Qt6 system packages (Bookworm)..."
    
    # Update and upgrade system packages automatically
    log "Updating package lists..."
    sudo apt update -qq
    
    log "Upgrading system packages automatically (no prompts)..."
    sudo DEBIAN_FRONTEND=noninteractive apt upgrade -y
    
    # Install Qt6 packages (available on Bookworm and newer)
    log "Installing Qt6 packages: python3-pyqt6, python3-pyqt6.qtwebengine, python3-pyqt6.qtsvg, python3-pyqt6-dev"
    
    # Also install essential build dependencies in case we need them later
    sudo DEBIAN_FRONTEND=noninteractive apt install -y build-essential python3-dev python3-pip
    
    if sudo DEBIAN_FRONTEND=noninteractive apt install -y python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6.qtsvg python3-pyqt6-dev; then
        success "Qt6 system packages installed"
        if test_pyqt6; then
            success "PyQt6 working with Qt6 system packages!"
            return 0
        else
            warning "Qt6 system packages installed but not working properly"
        fi
    else
        warning "Qt6 system packages installation failed"
    fi
    
    return 1
}

# Method 2: Pip with piwheels (medium speed)
try_pip_piwheels() {
    log "Method 2: Trying pip with piwheels..."
    
    # Use piwheels index for pre-compiled ARM packages
    if pip3 install --extra-index-url https://www.piwheels.org/simple/ PyQt6 PyQt6-WebEngine PyQt6-Svg; then
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
    
    if pip3 install PyQt6 PyQt6-WebEngine PyQt6-Svg; then
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

# Method 4: Build from source (automatic, no prompts)
try_build_from_source() {
    log "Method 4: Building Qt6 from source (automatic)..."
    warning "This will take several hours but requires no user interaction"
    
    log "Starting automatic Qt6 source build for Bookworm..."
    
    # Run the full build script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    bash "$SCRIPT_DIR/build_pyqt6_rpi.sh"
    return $?
}

# Main function
main() {
    log "Automated PyQt6 Quick Install for Raspberry Pi"
    log "================================================"
    log "This script automatically installs Qt6 with no user prompts"
    
    # Check if running on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        error "This script is designed for Raspberry Pi only!"
        error "For other systems, use: pip3 install PyQt6 PyQt6-WebEngine"
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
        error "All Qt6 installation methods failed!"
        error "You may need to:"
        error "1. Ensure you're running Raspberry Pi OS Bookworm or newer"
        error "2. Check your internet connection"
        error "3. Try running with sudo if permissions are an issue"
        error "4. Run the troubleshoot script: ./troubleshoot_pyqt6.sh"
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
