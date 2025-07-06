#!/usr/bin/env python3
"""
Version information for Office Kiosk Browser
"""

__version__ = "1.0.0"
__build_date__ = "2025-01-06"
__description__ = "Office Kiosk Browser - Touchscreen-friendly browser for Raspberry Pi"

def get_version_string():
    """Get formatted version string"""
    return f"v{__version__}"

def get_full_version_info():
    """Get full version information"""
    return {
        "version": __version__,
        "build_date": __build_date__,
        "description": __description__,
        "formatted": f"v{__version__} ({__build_date__})"
    }
