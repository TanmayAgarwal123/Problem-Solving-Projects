#!/usr/bin/env python3
"""
Simple test script to verify WhatsApp Web connection
"""

from whatsapp_automation import WhatsAppAutomation
import time

def test_whatsapp_connection():
    """Test basic WhatsApp Web connection"""
    print("=== WhatsApp Connection Test ===\n")
    
    try:
        # Initialize WhatsApp automation
        print("1. Initializing Chrome WebDriver...")
        whatsapp = WhatsAppAutomation()
        whatsapp.initialize_driver()
        print("✓ WebDriver initialized successfully")
        
        # Login to WhatsApp
        print("\n2. Opening WhatsApp Web...")
        print("   Please scan the QR code when it appears.")
        print("   Press Enter after you've successfully logged in...")
        
        if whatsapp.login_whatsapp(timeout=120):
            print("✓ Successfully logged in to WhatsApp Web")
            
            # Test sending a message
            test_number = input("\n3. Enter a phone number to test (with country code, e.g., +1234567890): ")
            test_message = "This is a test message from WhatsApp Pro Messenger"
            
            print(f"\n4. Attempting to send message to {test_number}...")
            if whatsapp.send_message(test_number, test_message):
                print("✓ Message sent successfully!")
            else:
                print("✗ Failed to send message")
            
            # Keep browser open for verification
            input("\n5. Check WhatsApp Web to verify the message was sent. Press Enter to close...")
            
        else:
            print("✗ Failed to login to WhatsApp Web")
        
        # Close the browser
        whatsapp.close()
        print("\n✓ Test completed")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure Chrome is installed")
        print("2. Check if ChromeDriver is in your PATH")
        print("3. Ensure ChromeDriver version matches your Chrome version")
        print("4. Try running with administrator privileges")

if __name__ == "__main__":
    test_whatsapp_connection()
