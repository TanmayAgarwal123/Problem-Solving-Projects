#!/usr/bin/env python3
"""
Diagnostic script to check Chrome and ChromeDriver setup
"""

import os
import sys
import subprocess
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import requests
import re

def check_chrome_installed():
    """Check if Chrome is installed"""
    print("1. Checking Chrome installation...")
    
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    if chrome_path:
        print(f"✓ Chrome found at: {chrome_path}")
        
        # Get Chrome version
        try:
            output = subprocess.check_output([chrome_path, "--version"], stderr=subprocess.DEVNULL)
            version = output.decode().strip()
            print(f"✓ Chrome version: {version}")
            
            # Extract version number
            version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
            if version_match:
                return version_match.group(1)
        except:
            print("⚠ Could not determine Chrome version")
    else:
        print("✗ Chrome not found in standard locations")
    
    return None

def check_chromedriver():
    """Check if ChromeDriver is installed and accessible"""
    print("\n2. Checking ChromeDriver...")
    
    chromedriver_path = shutil.which("chromedriver") or shutil.which("chromedriver.exe")
    
    if chromedriver_path:
        print(f"✓ ChromeDriver found at: {chromedriver_path}")
        
        # Get ChromeDriver version
        try:
            output = subprocess.check_output([chromedriver_path, "--version"], stderr=subprocess.DEVNULL)
            version = output.decode().strip()
            print(f"✓ ChromeDriver version: {version}")
            
            # Extract version number
            version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
            if version_match:
                return version_match.group(1)
        except:
            print("⚠ Could not determine ChromeDriver version")
    else:
        print("✗ ChromeDriver not found in PATH")
    
    return None

def check_version_compatibility(chrome_version, chromedriver_version):
    """Check if Chrome and ChromeDriver versions are compatible"""
    print("\n3. Checking version compatibility...")
    
    if chrome_version and chromedriver_version:
        chrome_major = chrome_version.split('.')[0]
        chromedriver_major = chromedriver_version.split('.')[0]
        
        if chrome_major == chromedriver_major:
            print(f"✓ Versions are compatible (both major version {chrome_major})")
            return True
        else:
            print(f"✗ Version mismatch! Chrome: {chrome_major}, ChromeDriver: {chromedriver_major}")
            return False
    else:
        print("⚠ Cannot check compatibility - missing version information")
        return False

def test_selenium_connection():
    """Test if Selenium can connect to Chrome"""
    print("\n4. Testing Selenium connection...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-features=NetworkService')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--window-size=1280,720')
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✓ Successfully started Chrome with Selenium")
        driver.get("https://www.google.com")
        print("✓ Successfully navigated to Google")
        driver.quit()
        return True
    except Exception as e:
        print(f"✗ Failed to start Chrome: {e}")
        return False

def download_chromedriver(chrome_version):
    """Provide instructions to download the correct ChromeDriver"""
    print("\n5. ChromeDriver Download Instructions:")
    
    if chrome_version:
        major_version = chrome_version.split('.')[0]
        print(f"You need ChromeDriver version {major_version}.x.x.x")
        print(f"Download from: https://chromedriver.chromium.org/downloads")
        print(f"Or try: https://googlechromelabs.github.io/chrome-for-testing/")
        
        # For newer Chrome versions
        if int(major_version) >= 115:
            print(f"\nFor Chrome {major_version}+, use the new download site:")
            print(f"https://googlechromelabs.github.io/chrome-for-testing/#stable")
    else:
        print("First install Google Chrome from: https://www.google.com/chrome/")

def main():
    print("=== Chrome & ChromeDriver Diagnostic Tool ===\n")
    
    # Check installations
    chrome_version = check_chrome_installed()
    chromedriver_version = check_chromedriver()
    
    # Check compatibility
    compatible = check_version_compatibility(chrome_version, chromedriver_version)
    
    # Test connection
    if chrome_version and chromedriver_version:
        test_selenium_connection()
    
    # Provide recommendations
    print("\n=== Recommendations ===")
    
    if not chrome_version:
        print("1. Install Google Chrome from: https://www.google.com/chrome/")
    
    if not chromedriver_version:
        print("2. Download ChromeDriver and add it to your PATH")
        download_chromedriver(chrome_version)
    
    if chrome_version and chromedriver_version and not compatible:
        print("3. Update ChromeDriver to match your Chrome version")
        download_chromedriver(chrome_version)
    
    print("\n=== Setup Instructions ===")
    print("1. Download the correct ChromeDriver version")
    print("2. Extract chromedriver.exe to a folder (e.g., C:\\WebDriver\\)")
    print("3. Add that folder to your system PATH:")
    print("   - Windows: System Properties → Environment Variables → PATH")
    print("   - Or place chromedriver.exe in your project directory")
    print("4. Restart your terminal/IDE after updating PATH")

if __name__ == "__main__":
    main()
