#!/usr/bin/env python3
"""
Test script to verify the application is ready for deployment.
Run this before deploying to Render to catch any issues early.
"""

import os
import sys
import subprocess
import importlib.util

def check_file_exists(filepath, description):
    """Check if a required file exists."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} - MISSING")
        return False

def check_requirements():
    """Check if all required packages can be imported."""
    required_packages = [
        'flask',
        'pandas', 
        'numpy',
        'openpyxl',
        'xlrd',
        'werkzeug'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ Package: {package}")
        except ImportError:
            print(f"✗ Package: {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def test_app_import():
    """Test if the Flask app can be imported without errors."""
    try:
        from app import app
        print("✓ Flask app imports successfully")
        return True
    except Exception as e:
        print(f"✗ Flask app import failed: {e}")
        return False

def main():
    print("🚀 Deployment Readiness Check")
    print("=" * 40)
    
    # Check required files
    files_ok = True
    files_ok &= check_file_exists("app.py", "Main application file")
    files_ok &= check_file_exists("requirements.txt", "Requirements file")
    files_ok &= check_file_exists("Procfile", "Procfile")
    files_ok &= check_file_exists("templates/index.html", "Index template")
    files_ok &= check_file_exists("templates/results.html", "Results template")
    
    print("\n📦 Package Dependencies")
    print("-" * 25)
    packages_ok = check_requirements()
    
    print("\n🔧 Application Test")
    print("-" * 20)
    app_ok = test_app_import()
    
    print("\n📊 Summary")
    print("-" * 10)
    if files_ok and packages_ok and app_ok:
        print("🎉 All checks passed! Your app is ready for deployment.")
        print("\nNext steps:")
        print("1. Push your code to GitHub")
        print("2. Connect your GitHub repo to Render")
        print("3. Deploy using the configuration in Procfile")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())