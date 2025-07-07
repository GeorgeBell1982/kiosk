#!/usr/bin/env python3
"""
Version information for Office Kiosk Browser
"""

__version__ = "2.0.0"
__build_date__ = "2025-01-07"
__description__ = "Office Kiosk Browser Qt6 - Modern touchscreen-friendly browser for Raspberry Pi"

def get_version_string():
    """Get formatted version string"""
    return f"v{__version__} Qt6"

def get_full_version_info():
    """Get full version information"""
    return {
        "version": __version__,
        "build_date": __build_date__,
        "description": __description__,
        "formatted": f"v{__version__} Qt6 ({__build_date__})"
    }
