from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import cv2
import pytesseract
import numpy as np
from PIL import Image
import io
import base64
from datetime import datetime

class WhatsAppAutomation:
    def __init__(self, ai_engine=None):
        self.driver = None
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        self.is_logged_in = False
        
    def initialize_driver(self, headless=False):
        """Initialize Chrome WebDriver with optimal settings"""
        options = webdriver.ChromeOptions()
        
        # Essential options to fix crashes
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=NetworkService')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-software-rasterizer')
        
        # Additional stability options
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Fix for Windows-specific issues
        options.add_argument('--disable-features=RendererCodeIntegrity')
        
        # Use a unique user data directory to avoid conflicts
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp(prefix='whatsapp_')
        options.add_argument(f'--user-data-dir={temp_dir}')
        
        if headless:
            options.add_argument('--headless')
        
        # Disable notifications
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 1
        }
        options.add_experimental_option("prefs", prefs)
        
        # Set binary location (adjust if Chrome is in a different location)
        import os
        if os.path.exists(r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
            options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        elif os.path.exists(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
            options.binary_location = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def login_whatsapp(self, timeout=60):
        """Login to WhatsApp Web"""
        try:
            self.driver.get("https://web.whatsapp.com")
            
            # Wait for QR code or main page
            wait = WebDriverWait(self.driver, timeout)
            
            # Check if already logged in
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '#side')))
                self.is_logged_in = True
                self.logger.info("Already logged in to WhatsApp")
                return True
            except TimeoutException:
                pass
            
            # Wait for QR code
            try:
                qr_element = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'canvas[aria-label="Scan me!"]')))
                self.logger.info("QR code found. Please scan to login.")
                
                # Wait for successful login
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '#side')))
                self.is_logged_in = True
                self.logger.info("Successfully logged in to WhatsApp")
                return True
            except TimeoutException:
                self.logger.error("Login timeout. QR code not scanned in time.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during WhatsApp login: {e}")
            return False
    
    def search_contact(self, contact_number):
        """Search for a contact by phone number"""
        try:
            # Click on search box
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[title="Search input textbox"]'))
            )
            search_box.click()
            
            # Clear and type contact
            search_box.send_keys(Keys.CONTROL + "a")
            search_box.send_keys(contact_number)
            time.sleep(2)
            
            # Select the contact
            contact = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'span[title*="{contact_number}"]'))
            )
            contact.click()
            time.sleep(1)
            return True
            
        except TimeoutException:
            self.logger.warning(f"Contact {contact_number} not found")
            return False
        except Exception as e:
            self.logger.error(f"Error searching contact {contact_number}: {e}")
            return False
    
    def send_message(self, contact_number, message, retry_count=3):
        """Send a message to a contact with retry mechanism"""
        for attempt in range(retry_count):
            try:
                if not self.search_contact(contact_number):
                    continue
                
                # Find message input box
                message_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[title="Type a message"]'))
                )
                
                # Type message
                message_box.click()
                message_box.send_keys(message)
                time.sleep(0.5)
                
                # Send message
                message_box.send_keys(Keys.ENTER)
                time.sleep(1)
                
                # Verify message was sent
                if self.verify_message_sent():
                    self.logger.info(f"Message sent to {contact_number}")
                    return True
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {contact_number}: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
        
        return False
    
    def verify_message_sent(self):
        """Verify if the last message was sent successfully"""
        try:
            # Check for the last message element
            messages = self.driver.find_elements(By.CSS_SELECTOR, 'div[class*="message-out"]')
            if messages:
                last_message = messages[-1]
                # Check for double tick or clock icon
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error verifying message: {e}")
            return False
    
    def check_delivery_status(self, contact_number):
        """Check delivery status of messages"""
        try:
            if not self.search_contact(contact_number):
                return None
            
            # Get all sent messages
            messages = self.driver.find_elements(By.CSS_SELECTOR, 'div[class*="message-out"]')
            
            statuses = []
            for message in messages[-5:]:  # Check last 5 messages
                try:
                    # Look for status icons (single tick, double tick, blue tick)
                    status_element = message.find_element(By.CSS_SELECTOR, 'span[data-icon]')
                    status_type = status_element.get_attribute('data-icon')
                    
                    if 'double-tick' in status_type:
                        statuses.append('delivered')
                    elif 'single-tick' in status_type:
                        statuses.append('sent')
                    else:
                        statuses.append('read')
                except:
                    statuses.append('unknown')
            
            return statuses
        except Exception as e:
            self.logger.error(f"Error checking delivery status: {e}")
            return None
    
    def capture_responses(self, contact_number, wait_time=30):
        """Capture responses from a contact"""
        try:
            if not self.search_contact(contact_number):
                return None
            
            # Wait for potential response
            time.sleep(wait_time)
            
            # Get incoming messages
            messages = self.driver.find_elements(By.CSS_SELECTOR, 'div[class*="message-in"]')
            
            responses = []
            for message in messages[-3:]:  # Get last 3 incoming messages
                try:
                    text_element = message.find_element(By.CSS_SELECTOR, 'span[class*="selectable-text"]')
                    text = text_element.text
                    
                    # Get timestamp
                    time_element = message.find_element(By.CSS_SELECTOR, 'span[dir="auto"]')
                    timestamp = time_element.text
                    
                    responses.append({
                        'text': text,
                        'timestamp': timestamp,
                        'sentiment': self.ai_engine.analyze_sentiment(text) if self.ai_engine else None
                    })
                except:
                    continue
            
            return responses
        except Exception as e:
            self.logger.error(f"Error capturing responses: {e}")
            return None
    
    def send_media(self, contact_number, media_path, caption=""):
        """Send media file with optional caption"""
        try:
            if not self.search_contact(contact_number):
                return False
            
            # Click attachment button
            attach_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[title="Attach"]'))
            )
            attach_btn.click()
            time.sleep(1)
            
            # Click image/video option
            media_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="file"]'))
            )
            media_option.send_keys(media_path)
            time.sleep(2)
            
            # Add caption if provided
            if caption:
                caption_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]'))
                )
                caption_box.send_keys(caption)
            
            # Send media
            send_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-icon="send"]'))
            )
            send_btn.click()
            
            return True
        except Exception as e:
            self.logger.error(f"Error sending media: {e}")
            return False
    
    def detect_online_status(self, contact_number):
        """Detect if a contact is online"""
        try:
            if not self.search_contact(contact_number):
                return None
            
            # Check for "online" or "typing" status
            try:
                status_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#main header span[title]'))
                )
                status_text = status_element.text.lower()
                
                if 'online' in status_text:
                    return 'online'
                elif 'typing' in status_text:
                    return 'typing'
                else:
                    return 'offline'
            except TimeoutException:
                return 'offline'
                
        except Exception as e:
            self.logger.error(f"Error detecting online status: {e}")
            return None
    
    def bulk_send_with_failover(self, messages_list, max_retries=3):
        """Send bulk messages with failover and recovery"""
        results = []
        failed_messages = []
        
        for msg_data in messages_list:
            contact = msg_data['contact']
            message = msg_data['message']
            
            # Try sending with retry mechanism
            success = False
            for retry in range(max_retries):
                try:
                    if self.send_message(contact, message):
                        success = True
                        results.append({
                            'contact': contact,
                            'status': 'sent',
                            'timestamp': datetime.now()
                        })
                        break
                except Exception as e:
                    self.logger.error(f"Retry {retry + 1} failed for {contact}: {e}")
                    time.sleep(5)  # Wait before retry
            
            if not success:
                failed_messages.append(msg_data)
                results.append({
                    'contact': contact,
                    'status': 'failed',
                    'timestamp': datetime.now()
                })
            
            # Smart delay between messages
            delay = self.calculate_smart_delay(len(results))
            time.sleep(delay)
        
        # Attempt recovery for failed messages
        if failed_messages:
            self.recover_failed_messages(failed_messages)
        
        return results
    
    def calculate_smart_delay(self, messages_sent):
        """Calculate smart delay based on messages sent"""
        import random
        
        # Increase delay as more messages are sent
        if messages_sent < 10:
            return random.uniform(30, 60)
        elif messages_sent < 50:
            return random.uniform(60, 120)
        else:
            return random.uniform(120, 240)
    
    def recover_failed_messages(self, failed_messages):
        """Attempt to recover failed messages"""
        self.logger.info(f"Attempting to recover {len(failed_messages)} failed messages")
        
        # Wait before recovery attempt
        time.sleep(300)  # 5 minutes
        
        # Refresh WhatsApp Web
        self.driver.refresh()
        time.sleep(10)
        
        # Retry failed messages
        for msg_data in failed_messages:
            try:
                self.send_message(msg_data['contact'], msg_data['message'])
            except Exception as e:
                self.logger.error(f"Recovery failed for {msg_data['contact']}: {e}")
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("WebDriver closed")