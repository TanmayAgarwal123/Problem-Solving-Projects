#!/usr/bin/env python3
"""
Simplified WhatsApp automation using alternative approach
"""

import time
import webbrowser
import pyautogui
try:
    import keyboard
except ImportError:
    keyboard = None
    print("Warning: keyboard module not found. Some features may not work.")
from urllib.parse import quote

class SimpleWhatsAppAutomation:
    def __init__(self):
        self.whatsapp_url = "https://web.whatsapp.com"
        
    def open_whatsapp(self):
        """Open WhatsApp Web in default browser"""
        print("Opening WhatsApp Web...")
        webbrowser.open(self.whatsapp_url)
        print("Please scan the QR code and press Enter when ready...")
        input()
        return True
    
    def send_message_url(self, phone, message):
        """Send message using WhatsApp URL scheme"""
        try:
            # Format phone number (remove +, spaces, etc.)
            phone_formatted = ''.join(filter(str.isdigit, str(phone)))
            
            # URL encode the message
            message_encoded = quote(message)
            
            # Create WhatsApp URL
            url = f"https://web.whatsapp.com/send?phone={phone_formatted}&text={message_encoded}"
            
            # Open URL
            webbrowser.open(url)
            
            # Wait for page to load
            time.sleep(8)
            
            # Press Enter to send (simulate key press)
            pyautogui.press('enter')
            
            print(f"Message sent to {phone}")
            return True
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def send_message_search(self, phone, message):
        """Send message by searching contact"""
        try:
            # Click on search box (you may need to adjust coordinates)
            print("Searching for contact...")
            time.sleep(2)
            
            # Use keyboard shortcut to focus search
            keyboard.press_and_release('ctrl+f')
            time.sleep(1)
            
            # Type phone number
            pyautogui.write(phone)
            time.sleep(3)
            
            # Press Enter to select contact
            pyautogui.press('enter')
            time.sleep(2)
            
            # Type message
            pyautogui.write(message)
            time.sleep(1)
            
            # Send message
            pyautogui.press('enter')
            
            print(f"Message sent to {phone}")
            return True
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def bulk_send(self, contacts, message, delay=30):
        """Send messages to multiple contacts"""
        print(f"Starting bulk send to {len(contacts)} contacts...")
        
        for i, contact in enumerate(contacts):
            phone = contact.get('phone', contact.get('Phone', ''))
            name = contact.get('name', contact.get('Name', ''))
            
            if not phone:
                continue
            
            # Personalize message
            personalized_msg = message.replace('{name}', name)
            personalized_msg = personalized_msg.replace('{first_name}', name.split()[0] if name else '')
            
            print(f"\nSending to {name} ({phone})...")
            
            # Try URL method first, fallback to search method
            success = self.send_message_url(phone, personalized_msg)
            
            if success:
                print(f"✓ Sent to {name}")
            else:
                print(f"✗ Failed to send to {name}")
            
            # Wait before next message
            if i < len(contacts) - 1:
                print(f"Waiting {delay} seconds before next message...")
                time.sleep(delay)
        
        print("\nBulk messaging completed!")

# Example usage
if __name__ == "__main__":
    # Test the simple automation
    wa = SimpleWhatsAppAutomation()
    
    print("=== Simple WhatsApp Automation Test ===")
    wa.open_whatsapp()
    
    # Test sending a single message
    test_number = input("Enter a phone number to test (with country code): ")
    test_message = "This is a test message from Simple WhatsApp Automation"
    
    if wa.send_message_url(test_number, test_message):
        print("Test successful!")
    else:
        print("Test failed!")