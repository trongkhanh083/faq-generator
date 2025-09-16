# install_playwright.py
import os
import subprocess
import sys

def install_playwright():
    """Install Playwright without root privileges"""
    print("Installing Playwright browsers without root...")
    
    try:
        # Install only Chromium (most reliable)
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium",
            "--with-deps", "false"  # Don't try to install system deps
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✓ Chromium installed successfully")
            return True
        else:
            print(f"Installation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Installation timed out")
        return False
    except Exception as e:
        print(f"Installation error: {e}")
        return False

if __name__ == "__main__":
    success = install_playwright()
    sys.exit(0 if success else 1)