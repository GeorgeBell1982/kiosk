#!/usr/bin/env python3
"""
Qt Version Test Script
Tests which Qt version is available and provides recommendations
"""

import sys

def test_qt_versions():
    """Test which Qt versions are available"""
    print("Qt Version Compatibility Test")
    print("=" * 40)
    
    # Test Qt6
    qt6_available = False
    qt6_webengine = False
    try:
        import PyQt6
        from PyQt6.QtWidgets import QApplication
        qt6_available = True
        print("✅ Qt6 (PyQt6) is available")
        
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            qt6_webengine = True
            print("✅ Qt6 WebEngine is available")
        except ImportError:
            print("❌ Qt6 WebEngine is NOT available")
            
    except ImportError:
        print("❌ Qt6 (PyQt6) is NOT available")
    
    # Test Qt5
    qt5_available = False
    qt5_webengine = False
    qt5_webkit = False
    try:
        import PyQt5
        from PyQt5.QtWidgets import QApplication
        qt5_available = True
        print("✅ Qt5 (PyQt5) is available")
        
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
            qt5_webengine = True
            print("✅ Qt5 WebEngine is available")
        except ImportError:
            print("❌ Qt5 WebEngine is NOT available")
            
        try:
            from PyQt5.QtWebKitWidgets import QWebView
            qt5_webkit = True
            print("✅ Qt5 WebKit is available (fallback)")
        except ImportError:
            print("❌ Qt5 WebKit is NOT available")
            
    except ImportError:
        print("❌ Qt5 (PyQt5) is NOT available")
    
    print("\nRecommendations:")
    print("-" * 40)
    
    if qt6_available and qt6_webengine:
        print("🎉 RECOMMENDED: Use Qt6 version (kiosk_browser.py)")
        print("   - Best modern web compatibility")
        print("   - YouTube should work without 'outdated browser' errors")
        print("   - Future-proof with active development")
        return "qt6"
    elif qt5_available and qt5_webengine:
        print("⚠️  ACCEPTABLE: Use Qt5 version (kiosk_browser_qt5_backup.py)")
        print("   - Good compatibility but may show 'outdated browser' warnings")
        print("   - Consider upgrading to newer Raspberry Pi OS for Qt6")
        return "qt5"
    elif qt5_available and qt5_webkit:
        print("⚠️  LIMITED: Use Qt5 with WebKit fallback")
        print("   - Basic web browsing only")
        print("   - Many modern sites may not work properly")
        return "qt5_webkit"
    else:
        print("❌ ERROR: No compatible Qt version found!")
        print("   Install packages:")
        print("   - For Qt6: sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine")
        print("   - For Qt5: sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine")
        return "none"

if __name__ == "__main__":
    result = test_qt_versions()
    
    print(f"\nResult: {result}")
    
    if result == "qt6":
        print("\n🚀 Ready to run: python3 kiosk_browser.py")
    elif result == "qt5":
        print("\n🚀 Ready to run: python3 kiosk_browser_qt5_backup.py")
        print("   Or copy it to kiosk_browser.py if you prefer Qt5")
    elif result == "qt5_webkit":
        print("\n⚠️  Limited functionality available")
    else:
        print("\n❌ Installation required before running")
        sys.exit(1)
