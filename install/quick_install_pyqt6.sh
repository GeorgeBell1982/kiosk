#!/bin/bash
# Quick PyQt6 Installation Script for Raspberry Pi (Bookworm+)
# Fully automated Qt6 installation with no Qt5 references
# Optimized for Raspberry Pi OS Bookworm and newer versions

set -e
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname -- "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
AUTOSTART_MODE=ask
ALLOW_SOURCE_BUILD=false

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
    local interpreter=python3
    if [ -x "$VENV_PYTHON" ]; then interpreter="$VENV_PYTHON"; fi
    "$interpreter" -c "
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
    
    # Refresh package metadata without upgrading unrelated system packages
    log "Updating package lists..."
    sudo apt update -qq || return 1
    
    # Install Qt6 packages (available on Bookworm and newer)
    log "Installing Qt6 packages: python3-pyqt6, python3-pyqt6.qtwebengine, python3-pyqt6.qtsvg, python3-pyqt6-dev"
    
    sudo DEBIAN_FRONTEND=noninteractive apt install -y python3-venv || return 1

    # Install virtual keyboard for touchscreen use
    log "Installing virtual keyboard (wvkbd) for touchscreen support..."
    sudo DEBIAN_FRONTEND=noninteractive apt install -y wvkbd || warning "wvkbd not available - virtual keyboard button will show installation instructions"
    
    if sudo DEBIAN_FRONTEND=noninteractive apt install -y python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6.qtsvg python3-pyqt6-dev; then
        success "Qt6 system packages installed"
        python3 -m venv --system-site-packages "$PROJECT_DIR/.venv" || return 1
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
    python3 -m venv --system-site-packages "$PROJECT_DIR/.venv" || return 1
    if "$VENV_PYTHON" -m pip install --extra-index-url https://www.piwheels.org/simple/ -r "$PROJECT_DIR/requirements.txt"; then
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
    
    python3 -m venv --system-site-packages "$PROJECT_DIR/.venv" || return 1
    if "$VENV_PYTHON" -m pip install -r "$PROJECT_DIR/requirements.txt"; then
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
    for option in "$@"; do
        case "$option" in
            --autostart) AUTOSTART_MODE=yes ;;
            --no-autostart) AUTOSTART_MODE=no ;;
            --build-from-source) ALLOW_SOURCE_BUILD=true ;;
            --help|-h)
                echo "Usage: bash install/quick_install_pyqt6.sh [--autostart|--no-autostart] [--build-from-source]"
                return 0 ;;
            *) error "Unknown option: $option"; return 2 ;;
        esac
    done
    if [ "$(id -u)" -eq 0 ]; then
        error "Run this installer as the desktop user; it invokes sudo only for OS packages."
        return 1
    fi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        error "This installer requires Raspberry Pi OS Bookworm or newer."
        return 1
    fi
    cd -- "$PROJECT_DIR"

    if test_pyqt6; then
        success "Qt6 with WebEngine is already installed."
    elif try_system_packages; then
        success "Installation successful via system packages."
    elif try_pip_piwheels; then
        success "Installation successful via virtual environment and piwheels."
    elif try_regular_pip; then
        success "Installation successful via virtual environment and pip."
    elif [ "$ALLOW_SOURCE_BUILD" = true ] && try_build_from_source; then
        success "Installation successful via source build."
    else
        error "Qt6 installation failed. See the diagnostics above."
        error "Source builds are optional: rerun with --build-from-source to allow one."
        return 1
    fi

    test_pyqt6 || { error "Final Qt6 verification failed"; return 1; }
    if [ "$AUTOSTART_MODE" = ask ]; then
        if [ -t 0 ]; then
            IFS= read -r -p "Enable desktop-login autostart? [Y/n]: " REPLY || REPLY=n
            if [[ -z "$REPLY" || "$REPLY" =~ ^[Yy]$ ]]; then
                AUTOSTART_MODE=yes
            else
                AUTOSTART_MODE=no
            fi
        else
            AUTOSTART_MODE=no
        fi
    fi
    if [ "$AUTOSTART_MODE" = yes ]; then
        bash "$SCRIPT_DIR/setup_autostart.sh" || return 1
    else
        log "Autostart unchanged. Enable it with: bash install/setup_autostart.sh"
    fi
    success "Ready. Start with: bash scripts/start_kiosk.sh"
}

main "$@"
