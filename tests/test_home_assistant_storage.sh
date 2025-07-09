#!/bin/bash
# Test Home Assistant storage and persistence

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

echo "🏠 Home Assistant Storage Test"
echo "=============================="
echo

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check storage directory
STORAGE_DIR="$HOME/.office_kiosk_data"
echo "📁 Checking storage configuration..."
echo "Storage directory: $STORAGE_DIR"

if [[ -d "$STORAGE_DIR" ]]; then
    success "✅ Storage directory exists"
    
    # Check permissions
    if [[ -w "$STORAGE_DIR" ]]; then
        success "✅ Storage directory is writable"
    else
        error "❌ Storage directory is not writable"
        ls -la "$STORAGE_DIR"
    fi
    
    # List contents
    echo
    echo "📋 Storage contents:"
    find "$STORAGE_DIR" -type f -name "*" 2>/dev/null | head -20 | while read -r file; do
        size=$(stat -c%s "$file" 2>/dev/null || echo "0")
        rel_path=$(realpath --relative-to="$STORAGE_DIR" "$file")
        echo "  $rel_path (${size} bytes)"
    done
    
    # Check for cookie-related files
    echo
    echo "🍪 Cookie and session files:"
    find "$STORAGE_DIR" -type f \( -name "*cookie*" -o -name "*session*" -o -name "*login*" -o -name "*auth*" \) 2>/dev/null | while read -r file; do
        size=$(stat -c%s "$file" 2>/dev/null || echo "0")
        rel_path=$(realpath --relative-to="$STORAGE_DIR" "$file")
        mtime=$(stat -c%y "$file" 2>/dev/null || echo "unknown")
        echo "  $rel_path (${size} bytes, modified: $mtime)"
    done
    
    # Check total storage size
    echo
    echo "💾 Storage usage:"
    du -sh "$STORAGE_DIR" 2>/dev/null || echo "  Unable to calculate size"
    
else
    warning "⚠️  Storage directory doesn't exist yet"
    echo "  Run the main application first to create it"
fi

echo
echo "🔧 Testing storage permissions..."

# Test creating a file
TEST_FILE="$STORAGE_DIR/test_write.tmp"
if mkdir -p "$STORAGE_DIR" 2>/dev/null && echo "test" > "$TEST_FILE" 2>/dev/null; then
    success "✅ Can create files in storage directory"
    rm -f "$TEST_FILE"
else
    error "❌ Cannot create files in storage directory"
    echo "  This will prevent login persistence"
fi

echo
echo "🐍 Testing Qt6 WebEngine storage..."

# Run the storage test script
if [[ -f "$SCRIPT_DIR/test_home_assistant_storage.py" ]]; then
    log "Running Qt6 storage test..."
    echo "  This will open a test window - check the console output for details"
    echo "  Use the buttons in the window to test storage functionality"
    echo
    
    python3 "$SCRIPT_DIR/test_home_assistant_storage.py" &
    TEST_PID=$!
    
    echo "Started storage test (PID: $TEST_PID)"
    echo "To stop the test: kill $TEST_PID"
else
    warning "Storage test script not found, creating it..."
    echo "Run this script again after the test script is created"
fi

echo
echo "📖 Storage Configuration Check:"
echo "==============================="

# Check the main app configuration
if [[ -f "$PROJECT_DIR/kiosk_browser.py" ]]; then
    echo "✅ Main application found"
    
    # Check for storage configuration in the code
    if grep -q "setPersistentStoragePath" "$PROJECT_DIR/kiosk_browser.py"; then
        success "✅ Persistent storage is configured in the app"
    else
        error "❌ Persistent storage not configured in the app"
    fi
    
    if grep -q "ForcePersistentCookies" "$PROJECT_DIR/kiosk_browser.py"; then
        success "✅ Persistent cookies are enabled"
    else
        error "❌ Persistent cookies not enabled"
    fi
    
    if grep -q "DiskHttpCache" "$PROJECT_DIR/kiosk_browser.py"; then
        success "✅ Disk HTTP cache is configured"
    else
        warning "⚠️  Disk HTTP cache not explicitly configured"
    fi
    
else
    error "❌ Main application not found"
fi

echo
echo "🏠 Home Assistant Recommendations:"
echo "=================================="
echo "1. Make sure your Home Assistant URL is added to the shortcuts"
echo "2. Try logging in and then completely close and restart the browser"
echo "3. Check if 'Remember this device' or similar option is enabled in HA"
echo "4. Verify your Home Assistant has persistent storage configured"
echo "5. Check that your HA session timeout is reasonable (not too short)"

echo
echo "🔍 Troubleshooting Steps:"
echo "========================"
echo "If login is not persisting:"
echo "1. Clear storage: rm -rf ~/.office_kiosk_data"
echo "2. Start the app fresh"
echo "3. Log into Home Assistant with 'Remember me' checked"
echo "4. Close the app completely"
echo "5. Start the app again and check if still logged in"

echo
echo "📱 Test Commands:"
echo "================="
echo "# Run storage test GUI:"
echo "python3 tests/test_home_assistant_storage.py"
echo
echo "# Check storage manually:"
echo "ls -la ~/.office_kiosk_data/"
echo "find ~/.office_kiosk_data -name '*cookie*' -o -name '*session*'"
echo
echo "# Clear storage (for testing):"
echo "rm -rf ~/.office_kiosk_data"

echo
