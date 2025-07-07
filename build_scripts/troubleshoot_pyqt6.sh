#!/bin/bash
# PyQt6 Installation Troubleshooter for Raspberry Pi
# Diagnoses and fixes common PyQt6 installation issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# System information
gather_system_info() {
    log "Gathering system information..."
    
    echo "=== SYSTEM INFO ==="
    echo "Date: $(date)"
    echo "Hostname: $(hostname)"
    echo "Uptime: $(uptime)"
    echo
    
    echo "=== RASPBERRY PI INFO ==="
    if [ -f /proc/cpuinfo ]; then
        grep "Model\|Hardware\|Revision" /proc/cpuinfo
    fi
    echo
    
    echo "=== OS INFO ==="
    if [ -f /etc/os-release ]; then
        cat /etc/os-release
    fi
    echo
    
    echo "=== MEMORY INFO ==="
    free -h
    echo
    
    echo "=== DISK SPACE ==="
    df -h /
    echo
    
    echo "=== PYTHON INFO ==="
    python3 --version
    pip3 --version
    echo
}

# Check Qt installations
check_qt_installations() {
    log "Checking Qt installations..."
    
    echo "=== QT PACKAGES ==="
    dpkg -l | grep -i qt | head -20
    echo
    
    echo "=== QT BINARIES ==="
    for qt_bin in qmake qmake6 /usr/bin/qmake* /usr/share/qt*/bin/qmake*; do
        if [ -x "$qt_bin" ]; then
            echo "Found: $qt_bin"
            "$qt_bin" -version 2>/dev/null || echo "  (version check failed)"
        fi
    done
    echo
    
    echo "=== QT LIBRARIES ==="
    find /usr/lib* -name "*Qt*" -type d 2>/dev/null | head -10
    echo
}

# Check Python installations
check_python_installations() {
    log "Checking Python installations..."
    
    echo "=== PYTHON PACKAGES ==="
    pip3 list | grep -i pyqt
    echo
    
    echo "=== PYTHON PATHS ==="
    python3 -c "import sys; print('\\n'.join(sys.path))"
    echo
    
    echo "=== PYTHON IMPORT TEST ==="
    python3 -c "
try:
    import PyQt6
    print('PyQt6: AVAILABLE')
    print(f'PyQt6 location: {PyQt6.__file__}')
    try:
        from PyQt6 import QtCore
        print(f'Qt version: {QtCore.QT_VERSION_STR}')
        print(f'PyQt version: {QtCore.PYQT_VERSION_STR}')
    except:
        pass
except ImportError as e:
    print(f'PyQt6: NOT AVAILABLE - {e}')

try:
    import PyQt5
    print('PyQt5: AVAILABLE')
    print(f'PyQt5 location: {PyQt5.__file__}')
except ImportError as e:
    print(f'PyQt5: NOT AVAILABLE - {e}')
"
    echo
}

# Check for common issues
check_common_issues() {
    log "Checking for common issues..."
    
    echo "=== COMMON ISSUES ==="
    
    # Check GPU memory
    if command -v vcgencmd >/dev/null 2>&1; then
        GPU_MEM=$(vcgencmd get_mem gpu | cut -d= -f2 | cut -dM -f1)
        echo "GPU Memory: ${GPU_MEM}MB"
        if [ "$GPU_MEM" -lt 64 ]; then
            warning "GPU memory is only ${GPU_MEM}MB. Recommend at least 64MB for Qt applications."
            echo "  Fix: Add 'gpu_mem=64' to /boot/config.txt and reboot"
        fi
    fi
    
    # Check X11
    if [ -z "$DISPLAY" ]; then
        warning "DISPLAY variable not set"
        echo "  This suggests you're not in a graphical session"
        echo "  Qt GUI applications need a display server"
    else
        echo "DISPLAY: $DISPLAY"
        if command -v xset >/dev/null 2>&1; then
            if xset q >/dev/null 2>&1; then
                success "X11 display server is accessible"
            else
                warning "X11 display server not accessible"
            fi
        fi
    fi
    
    # Check for conflicting installations
    PYQT_LOCATIONS=$(python3 -c "
import sys
locations = []
try:
    import PyQt6
    locations.append(f'PyQt6: {PyQt6.__file__}')
except:
    pass
try:
    import PyQt5
    locations.append(f'PyQt5: {PyQt5.__file__}')
except:
    pass
for loc in locations:
    print(loc)
" 2>/dev/null)
    
    if [ -n "$PYQT_LOCATIONS" ]; then
        echo "PyQt installations found:"
        echo "$PYQT_LOCATIONS"
    fi
    
    echo
}

# Fix common issues
fix_common_issues() {
    log "Attempting to fix common issues..."
    
    # Update package lists
    log "Updating package lists..."
    sudo apt update -qq
    
    # Install missing system dependencies
    log "Installing system dependencies..."
    sudo apt install -y \
        python3-dev \
        python3-pip \
        build-essential \
        pkg-config \
        libxcb-xinerama0-dev \
        libgl1-mesa-dev \
        libglib2.0-dev \
        libfontconfig1-dev \
        libx11-xcb-dev \
        libglu1-mesa-dev \
        libxrender-dev \
        libxi-dev \
        libxkbcommon-dev \
        libxkbcommon-x11-dev 2>/dev/null || warning "Some dependencies may not be available"
    
    # Fix pip issues
    log "Upgrading pip..."
    python3 -m pip install --upgrade pip setuptools wheel
    
    # Clean pip cache
    log "Cleaning pip cache..."
    pip3 cache purge 2>/dev/null || true
    
    success "Common fixes applied"
}

# Test PyQt6 functionality
test_pyqt6_functionality() {
    log "Testing PyQt6 functionality..."
    
    cat > /tmp/pyqt6_test.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

def test_imports():
    results = {}
    
    # Test core PyQt6
    try:
        from PyQt6.QtWidgets import QApplication, QWidget, QPushButton
        from PyQt6.QtCore import QTimer, Qt
        from PyQt6.QtGui import QIcon, QFont
        results['PyQt6_Core'] = 'OK'
    except ImportError as e:
        results['PyQt6_Core'] = f'FAILED: {e}'
    
    # Test WebEngine
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebEngineCore import QWebEngineSettings
        results['PyQt6_WebEngine'] = 'OK'
    except ImportError as e:
        results['PyQt6_WebEngine'] = f'FAILED: {e}'
    
    # Test basic functionality
    try:
        app = QApplication(sys.argv)
        widget = QWidget()
        widget.setWindowTitle("Test")
        app.processEvents()
        app.quit()
        results['PyQt6_Functionality'] = 'OK'
    except Exception as e:
        results['PyQt6_Functionality'] = f'FAILED: {e}'
    
    return results

if __name__ == "__main__":
    print("PyQt6 Functionality Test")
    print("=" * 30)
    
    results = test_imports()
    
    for test, result in results.items():
        status = "✓" if result == "OK" else "✗"
        print(f"{status} {test}: {result}")
    
    # Overall result
    all_core_ok = results.get('PyQt6_Core') == 'OK' and results.get('PyQt6_Functionality') == 'OK'
    webengine_ok = results.get('PyQt6_WebEngine') == 'OK'
    
    if all_core_ok and webengine_ok:
        print("\n🎉 All tests passed! PyQt6 is fully functional.")
        sys.exit(0)
    elif all_core_ok:
        print("\n⚠️  Core PyQt6 works but WebEngine has issues.")
        sys.exit(1)
    else:
        print("\n❌ PyQt6 core functionality failed.")
        sys.exit(2)
EOF
    
    python3 /tmp/pyqt6_test.py
    TEST_RESULT=$?
    rm -f /tmp/pyqt6_test.py
    
    return $TEST_RESULT
}

# Generate report
generate_report() {
    log "Generating diagnostic report..."
    
    REPORT_FILE="/tmp/pyqt6_diagnostic_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "PyQt6 Diagnostic Report"
        echo "======================"
        echo "Generated: $(date)"
        echo
        
        gather_system_info
        check_qt_installations
        check_python_installations
        check_common_issues
        
        echo "=== TEST RESULTS ==="
        if test_pyqt6_functionality; then
            echo "PyQt6 functionality: PASSED"
        else
            echo "PyQt6 functionality: FAILED"
        fi
        echo
        
    } > "$REPORT_FILE"
    
    success "Diagnostic report saved to: $REPORT_FILE"
    
    # Show summary
    log "=== DIAGNOSTIC SUMMARY ==="
    if test_pyqt6_functionality; then
        success "PyQt6 appears to be working correctly"
    else
        error "PyQt6 has issues that need to be addressed"
        warning "Try running: ./quick_install_pyqt6.sh"
    fi
}

# Main function
main() {
    log "PyQt6 Troubleshooter for Raspberry Pi"
    log "====================================="
    
    case "${1:-all}" in
        "info")
            gather_system_info
            ;;
        "qt")
            check_qt_installations
            ;;
        "python")
            check_python_installations
            ;;
        "issues")
            check_common_issues
            ;;
        "fix")
            fix_common_issues
            ;;
        "test")
            test_pyqt6_functionality
            ;;
        "report")
            generate_report
            ;;
        "all"|*)
            gather_system_info
            check_qt_installations
            check_python_installations
            check_common_issues
            fix_common_issues
            test_pyqt6_functionality
            ;;
    esac
}

# Show usage if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  info     - Show system information"
    echo "  qt       - Check Qt installations"
    echo "  python   - Check Python installations"
    echo "  issues   - Check for common issues"
    echo "  fix      - Fix common issues"
    echo "  test     - Test PyQt6 functionality"
    echo "  report   - Generate full diagnostic report"
    echo "  all      - Run all checks and fixes (default)"
    echo
    exit 0
fi

main "$@"
