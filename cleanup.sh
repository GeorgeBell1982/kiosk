#!/bin/bash
# Repository Cleanup and Optimization Script

echo "Office Kiosk Browser - Repository Cleanup"
echo "========================================="

# Remove Python cache files
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove editor backup files
echo "Cleaning editor backups..."
find . -name "*~" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*.orig" -delete 2>/dev/null || true

# Remove OS-specific files
echo "Cleaning OS files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true
find . -name "desktop.ini" -delete 2>/dev/null || true

# Set executable permissions on scripts
echo "Setting script permissions..."
chmod +x install/*.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x tests/*.py 2>/dev/null || true
chmod +x kiosk_browser.py 2>/dev/null || true

# Verify directory structure
echo "Verifying structure..."
for dir in install tests scripts systemd docs icons legacy; do
    if [ -d "$dir" ]; then
        echo "✓ $dir/ directory exists"
    else
        echo "✗ $dir/ directory missing"
    fi
done

# Check key files
echo "Checking key files..."
for file in kiosk_browser.py config.ini requirements.txt version.py; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
    fi
done

echo
echo "Cleanup complete!"
echo
echo "Repository structure:"
echo "  📁 install/     - Installation scripts"
echo "  📁 tests/       - Test utilities"  
echo "  📁 scripts/     - Helper scripts"
echo "  📁 systemd/     - Service files"
echo "  📁 docs/        - Documentation"
echo "  📁 icons/       - SVG assets"
echo "  📁 legacy/      - Qt5 backup"
echo "  📄 kiosk_browser.py - Main application"
echo "  📄 README.md    - Quick start guide"
echo
echo "Next steps:"
echo "  1. Run: ./install/quick_install_pyqt6.sh"
echo "  2. Test: python3 kiosk_browser.py"
echo "  3. Read: docs/README.md"
