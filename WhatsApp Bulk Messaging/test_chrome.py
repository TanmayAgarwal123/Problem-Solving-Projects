#!/usr/bin/env python3
"""
Test script to verify Chrome and WhatsApp setup
"""

from whatsapp_automation import WhatsAppAutomation
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_whatsapp_connection():
    """Test WhatsApp connection"""
    print("=== WhatsApp Connection Test ===\n")
    
    try:
        # Initialize WhatsApp automation
        print("1. Initializing Chrome WebDriver...")
        whatsapp = WhatsAppAutomation()
        whatsapp.initialize_driver()
        print("✓ Chrome initialized successfully")
        
        # Open WhatsApp Web
        print("\n2. Opening WhatsApp Web...")
        if whatsapp.login_whatsapp(timeout=120):
            print("✓ Successfully logged in to WhatsApp")
            
            # Test sending a message
            test_number = input("\n3. Enter a phone number to test (with country code, e.g., +1234567890): ")
            test_message = "This is a test message from WhatsApp Pro Messenger"
            
            print(f"\n4. Sending test message to {test_number}...")
            if whatsapp.send_message(test_number, test_message):
                print("✓ Message sent successfully!")
            else:
                print("✗ Failed to send message")
            
            # Keep browser open for verification
            input("\n5. Press Enter to close the browser...")
        else:
            print("✗ Failed to login to WhatsApp")
        
        # Close browser
        whatsapp.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Chrome is installed")
        print("2. Install ChromeDriver matching your Chrome version")
        print("3. Close all Chrome windows and try again")
        print("4. Run as administrator if needed")

if __name__ == "__main__":
    test_whatsapp_connection()
