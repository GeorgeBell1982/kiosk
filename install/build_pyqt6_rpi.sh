#!/bin/bash
# PyQt6 Build Script for Raspberry Pi
# Automated build and installation of PyQt6 from source

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
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

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        error "This script is designed for Raspberry Pi only!"
        exit 1
    fi
    
    PI_MODEL=$(cat /proc/cpuinfo | grep "Model" | head -1 | cut -d':' -f2 | xargs)
    log "Detected: $PI_MODEL"
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check available disk space (need at least 5GB)
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=5242880  # 5GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        error "Insufficient disk space. Need at least 5GB free."
        exit 1
    fi
    
    # Check RAM (recommend at least 1GB)
    TOTAL_RAM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    if [ "$TOTAL_RAM" -lt 1048576 ]; then  # 1GB in KB
        warning "Less than 1GB RAM detected. Build may be slow or fail."
        warning "Consider adding swap space or using a more powerful Pi."
    fi
    
    success "System requirements check passed"
}

# Optimize build settings based on Pi model
set_build_optimization() {
    log "Setting build optimizations..."
    
    case "$PI_MODEL" in
        *"Pi 5"*)
            JOBS=$(nproc)
            MEMORY_LIMIT=""
            BUILD_TYPE="optimized"
            ;;
        *"Pi 4"*)
            JOBS=$(nproc)
            MEMORY_LIMIT=""
            BUILD_TYPE="standard"
            ;;
        *"Pi 3"*)
            JOBS=2
            MEMORY_LIMIT="limited"
            BUILD_TYPE="conservative"
            ;;
        *)
            JOBS=1
            MEMORY_LIMIT="minimal"
            BUILD_TYPE="minimal"
            ;;
    esac
    
    log "Build configuration: $BUILD_TYPE (using $JOBS jobs)"
    
    # Set environment variables for optimization
    export MAKEFLAGS="-j$JOBS"
    export CXXFLAGS="-O2 -pipe"
    export CFLAGS="-O2 -pipe"
}

# Setup swap if needed
setup_swap() {
    log "Checking swap configuration..."
    
    SWAP_SIZE=$(swapon --show=SIZE --noheadings --bytes | head -1)
    if [ -z "$SWAP_SIZE" ] || [ "$SWAP_SIZE" -lt 2147483648 ]; then  # Less than 2GB
        warning "Insufficient swap space detected. Adding temporary swap..."
        
        sudo fallocate -l 2G /tmp/build_swap || {
            error "Failed to create swap file"
            exit 1
        }
        sudo chmod 600 /tmp/build_swap
        sudo mkswap /tmp/build_swap
        sudo swapon /tmp/build_swap
        
        success "Temporary 2GB swap added"
        SWAP_ADDED=true
    else
        SWAP_ADDED=false
    fi
}

# Install build dependencies
install_dependencies() {
    log "Installing build dependencies..."
    
    # Update package lists
    sudo apt update -qq
    
    # Essential build tools
    sudo apt install -y \
        build-essential \
        git \
        cmake \
        ninja-build \
        python3-dev \
        python3-pip \
        python3-venv \
        pkg-config
    
    # Qt6 development packages (if available)
    if sudo apt install -y qt6-base-dev qt6-webengine-dev qt6-tools-dev 2>/dev/null; then
        success "Qt6 development packages installed"
        QT6_SYSTEM=true
    else
        warning "Qt6 system packages not available, will build minimal Qt6"
        QT6_SYSTEM=false
        
        # Install additional dependencies for Qt6 build
        sudo apt install -y \
            libfontconfig1-dev \
            libfreetype6-dev \
            libx11-dev \
            libx11-xcb-dev \
            libxext-dev \
            libxfixes-dev \
            libxi-dev \
            libxrender-dev \
            libxcb1-dev \
            libxcb-cursor-dev \
            libxcb-glx0-dev \
            libxcb-keysyms1-dev \
            libxcb-image0-dev \
            libxcb-shm0-dev \
            libxcb-icccm4-dev \
            libxcb-sync-dev \
            libxcb-xfixes0-dev \
            libxcb-shape0-dev \
            libxcb-randr0-dev \
            libxcb-render-util0-dev \
            libxcb-util-dev \
            libxcb-xinerama0-dev \
            libxcb-xkb-dev \
            libxkbcommon-dev \
            libxkbcommon-x11-dev \
            libgl1-mesa-dev \
            libglu1-mesa-dev \
            libasound2-dev
    fi
    
    success "Dependencies installed"
}

# Build or install Qt6
setup_qt6() {
    if [ "$QT6_SYSTEM" = true ]; then
        log "Using system Qt6 packages"
        return 0
    fi
    
    log "Building minimal Qt6 from source..."
    warning "This will take 4-8 hours depending on your Pi model!"
    
    read -p "Continue with Qt6 build? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Qt6 build cancelled by user"
        exit 1
    fi
    
    QT6_BUILD_DIR="$BUILD_DIR/qt6_build"
    mkdir -p "$QT6_BUILD_DIR"
    cd "$QT6_BUILD_DIR"
    
    # Download Qt6 source (minimal version)
    QT_VERSION="6.6.1"
    if [ ! -f "qt-everywhere-src-$QT_VERSION.tar.xz" ]; then
        log "Downloading Qt6 source..."
        wget "https://download.qt.io/official_releases/qt/6.6/$QT_VERSION/single/qt-everywhere-src-$QT_VERSION.tar.xz"
    fi
    
    if [ ! -d "qt-everywhere-src-$QT_VERSION" ]; then
        log "Extracting Qt6 source..."
        tar -xf "qt-everywhere-src-$QT_VERSION.tar.xz"
    fi
    
    cd "qt-everywhere-src-$QT_VERSION"
    
    # Configure Qt6 with minimal features for Pi
    log "Configuring Qt6 build..."
    ./configure \
        -opensource \
        -confirm-license \
        -release \
        -shared \
        -strip \
        -no-opengl \
        -no-vulkan \
        -no-feature-vulkan \
        -nomake examples \
        -nomake tests \
        -skip qtwebengine \
        -skip qt3d \
        -skip qtquick3d \
        -skip qtmultimedia \
        -prefix /opt/qt6-minimal
    
    # Build Qt6
    log "Building Qt6 (this will take several hours)..."
    cmake --build . --parallel $JOBS
    
    # Install Qt6
    log "Installing Qt6..."
    sudo cmake --install .
    
    # Set up environment
    export PATH="/opt/qt6-minimal/bin:$PATH"
    export LD_LIBRARY_PATH="/opt/qt6-minimal/lib:$LD_LIBRARY_PATH"
    export PKG_CONFIG_PATH="/opt/qt6-minimal/lib/pkgconfig:$PKG_CONFIG_PATH"
    
    success "Qt6 built and installed to /opt/qt6-minimal"
}

# Build PyQt6
build_pyqt6() {
    log "Building PyQt6..."
    
    PYQT6_BUILD_DIR="$BUILD_DIR/pyqt6_build"
    mkdir -p "$PYQT6_BUILD_DIR"
    cd "$PYQT6_BUILD_DIR"
    
    # Create virtual environment for build
    log "Setting up build environment..."
    python3 -m venv build_env
    source build_env/bin/activate
    
    # Install build requirements
    pip install --upgrade pip setuptools wheel
    pip install sip PyQt6-sip
    
    # Download PyQt6 source
    PYQT6_VERSION="6.6.1"
    if [ ! -f "PyQt6-$PYQT6_VERSION.tar.gz" ]; then
        log "Downloading PyQt6 source..."
        wget "https://files.pythonhosted.org/packages/source/P/PyQt6/PyQt6-$PYQT6_VERSION.tar.gz"
    fi
    
    if [ ! -d "PyQt6-$PYQT6_VERSION" ]; then
        log "Extracting PyQt6 source..."
        tar -xzf "PyQt6-$PYQT6_VERSION.tar.gz"
    fi
    
    cd "PyQt6-$PYQT6_VERSION"
    
    # Find qmake6
    QMAKE6_PATH=""
    for path in /usr/bin/qmake6 /opt/qt6-minimal/bin/qmake /usr/share/qt6/bin/qmake; do
        if [ -x "$path" ]; then
            QMAKE6_PATH="$path"
            break
        fi
    done
    
    if [ -z "$QMAKE6_PATH" ]; then
        error "qmake6 not found! Qt6 installation may be incomplete."
        exit 1
    fi
    
    log "Using qmake6 at: $QMAKE6_PATH"
    
    # Configure PyQt6 build
    log "Configuring PyQt6 build..."
    python configure.py \
        --qmake "$QMAKE6_PATH" \
        --sip-module PyQt6.sip \
        --confirm-license \
        --verbose \
        --no-docstrings \
        --no-tools
    
    # Build PyQt6
    log "Building PyQt6 (this will take 1-3 hours)..."
    make -j$JOBS
    
    # Install PyQt6
    log "Installing PyQt6..."
    sudo make install
    
    success "PyQt6 built and installed successfully!"
}

# Build PyQt6-WebEngine (optional)
build_webengine() {
    log "Attempting to build PyQt6-WebEngine..."
    warning "WebEngine build is experimental and may fail on some Pi models"
    
    read -p "Attempt WebEngine build? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        warning "Skipping WebEngine build"
        return 0
    fi
    
    cd "$BUILD_DIR"
    
    # Try to install WebEngine via pip first
    if pip3 install PyQt6-WebEngine; then
        success "PyQt6-WebEngine installed via pip"
        return 0
    fi
    
    warning "WebEngine pip install failed, skipping WebEngine support"
    return 1
}

# Test the installation
test_installation() {
    log "Testing PyQt6 installation..."
    
    # Create test script
    cat > /tmp/test_pyqt6_build.py << 'EOF'
#!/usr/bin/env python3
import sys
import traceback

def test_pyqt6():
    try:
        print("Testing PyQt6 import...")
        from PyQt6.QtWidgets import QApplication, QWidget
        print("✓ PyQt6.QtWidgets imported successfully")
        
        from PyQt6.QtCore import QTimer, pyqtSignal
        print("✓ PyQt6.QtCore imported successfully")
        
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            print("✓ PyQt6.QtWebEngineWidgets imported successfully")
            webengine_available = True
        except ImportError as e:
            print(f"✗ QtWebEngine not available: {e}")
            webengine_available = False
        
        # Test basic functionality
        app = QApplication(sys.argv)
        widget = QWidget()
        widget.setWindowTitle("PyQt6 Build Test")
        widget.resize(300, 200)
        
        print("✓ Basic PyQt6 functionality working")
        print(f"PyQt6 version: {app.applicationVersion()}")
        
        app.quit()
        return webengine_available
        
    except Exception as e:
        print(f"✗ PyQt6 test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    webengine_ok = test_pyqt6()
    if webengine_ok:
        print("\n🎉 PyQt6 with WebEngine built successfully!")
        exit(0)
    else:
        print("\n⚠️  PyQt6 built but WebEngine may have issues")
        exit(1)
EOF
    
    if python3 /tmp/test_pyqt6_build.py; then
        success "PyQt6 installation test passed!"
        return 0
    else
        error "PyQt6 installation test failed!"
        return 1
    fi
}

# Cleanup
cleanup() {
    log "Cleaning up..."
    
    # Remove temporary swap if we added it
    if [ "$SWAP_ADDED" = true ]; then
        sudo swapoff /tmp/build_swap 2>/dev/null || true
        sudo rm -f /tmp/build_swap
        success "Temporary swap removed"
    fi
    
    # Clean up temporary files
    rm -f /tmp/test_pyqt6_build.py
    
    log "Cleanup complete"
}

# Main execution
main() {
    log "Starting PyQt6 build for Raspberry Pi"
    log "======================================="
    
    # Setup
    check_raspberry_pi
    check_requirements
    set_build_optimization
    setup_swap
    
    # Create build directory
    BUILD_DIR="$HOME/pyqt6_build_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BUILD_DIR"
    log "Build directory: $BUILD_DIR"
    
    # Build process
    install_dependencies
    setup_qt6
    build_pyqt6
    build_webengine
    
    # Test and finish
    if test_installation; then
        success "PyQt6 build completed successfully!"
        success "You can now use PyQt6 in your Python applications"
        
        # Update the kiosk browser to use the new PyQt6
        log "Updating kiosk browser configuration..."
        cd "$HOME/office_kiosk" 2>/dev/null || {
            warning "Office kiosk directory not found at $HOME/office_kiosk"
            warning "You may need to update your kiosk browser manually"
        }
        
        success "Build process completed!"
        success "You can now run: python3 test_qt_version.py"
        success "And then: python3 kiosk_browser.py"
        
    else
        error "PyQt6 build completed but tests failed"
        error "Check the logs above for details"
        exit 1
    fi
}

# Handle interrupts
trap cleanup EXIT INT TERM

# Run main function
main "$@"
