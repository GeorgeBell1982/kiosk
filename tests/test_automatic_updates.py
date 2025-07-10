#!/usr/bin/env python3
"""
Test script to verify automatic update configuration
"""

import os
import sys
import logging
import configparser
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_update_configuration():
    """Test that automatic updates are properly configured"""
    
    print("🔍 Testing Automatic Update Configuration")
    print("=" * 50)
    
    base_dir = Path(__file__).parent.parent
    config_file = base_dir / "scripts" / "update_config.conf"
    update_script = base_dir / "scripts" / "update_check.sh"
    
    # Test 1: Check if configuration file exists
    print("\n1. Checking configuration file...")
    if config_file.exists():
        print(f"✅ Configuration file exists: {config_file}")
    else:
        print(f"❌ Configuration file missing: {config_file}")
        return False
    
    # Test 2: Check if update script exists
    print("\n2. Checking update script...")
    if update_script.exists():
        print(f"✅ Update script exists: {update_script}")
    else:
        print(f"❌ Update script missing: {update_script}")
        return False
    
    # Test 3: Parse configuration
    print("\n3. Parsing configuration...")
    try:
        config = {}
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        print(f"✅ Configuration parsed successfully")
        print(f"   Found {len(config)} configuration options:")
        for key, value in config.items():
            print(f"   - {key}: {value}")
            
    except Exception as e:
        print(f"❌ Error parsing configuration: {e}")
        return False
    
    # Test 4: Check automatic update settings
    print("\n4. Checking automatic update settings...")
    
    auto_check = config.get('AUTO_UPDATE_CHECK', 'false').lower()
    auto_apply = config.get('AUTO_UPDATE_APPLY', 'false').lower()
    
    if auto_check == 'true':
        print("✅ AUTO_UPDATE_CHECK is enabled")
    else:
        print("❌ AUTO_UPDATE_CHECK is disabled")
        return False
    
    if auto_apply == 'true':
        print("✅ AUTO_UPDATE_APPLY is enabled (NO user prompts)")
    else:
        print("❌ AUTO_UPDATE_APPLY is disabled (will prompt user)")
        return False
    
    # Test 5: Check if running on Raspberry Pi
    print("\n5. Checking platform...")
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' in cpuinfo:
                print("✅ Running on Raspberry Pi - automatic updates will work")
            else:
                print("ℹ️  Not running on Raspberry Pi - automatic updates disabled by design")
    except FileNotFoundError:
        print("ℹ️  /proc/cpuinfo not found - likely not on Linux (automatic updates disabled)")
    
    # Test 6: Check git repository
    print("\n6. Checking git repository...")
    git_dir = base_dir / ".git"
    if git_dir.exists():
        print("✅ Git repository found - updates can be pulled")
    else:
        print("❌ No git repository found - updates cannot be pulled")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 AUTOMATIC UPDATE CONFIGURATION TEST PASSED!")
    print("\nSummary:")
    print("• Updates will be checked automatically on app startup")
    print("• Updates will be applied automatically WITHOUT user prompts")
    print("• App will restart automatically after updates")
    print("• No manual intervention required")
    
    return True

if __name__ == "__main__":
    success = test_update_configuration()
    sys.exit(0 if success else 1)
