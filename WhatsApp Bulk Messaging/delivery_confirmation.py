import cv2
import numpy as np
import pytesseract
from PIL import Image
import time
import logging
from datetime import datetime, timedelta
import sqlite3
import json
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class DeliveryConfirmationSystem:
    def __init__(self, driver=None, db_path='whatsapp_pro.db'):
        self.driver = driver
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Status icon templates for computer vision
        self.status_icons = {
            'sent': 'single_tick',
            'delivered': 'double_tick', 
            'read': 'blue_tick',
            'failed': 'clock_icon'
        }
    
    def check_message_status(self, contact, message_id):
        """Check the delivery status of a specific message"""
        try:
            # Navigate to contact
            if not self.navigate_to_contact(contact):
                return 'unknown'
            
            # Find the message element
            message_element = self.find_message_element(message_id)
            if not message_element:
                return 'not_found'
            
            # Check status icons
            status = self.detect_status_icon(message_element)
            
            # Update database
            self.update_message_status(message_id, status)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error checking message status: {e}")
            return 'error'
    
    def navigate_to_contact(self, contact):
        """Navigate to a specific contact's chat"""
        try:
            # Search for contact
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[title="Search input textbox"]'))
            )
            search_box.click()
            search_box.clear()
            search_box.send_keys(contact)
            time.sleep(2)
            
            # Click on contact
            contact_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'span[title*="{contact}"]'))
            )
            contact_element.click()
            time.sleep(1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error navigating to contact {contact}: {e}")
            return False
    
    def find_message_element(self, message_id):
        """Find a specific message element in the chat"""
        try:
            # Get message from database to match content
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT message FROM messages WHERE id = ?', (message_id,))
            message_content = cursor.fetchone()[0]
            conn.close()
            
            # Find all sent messages
            messages = self.driver.find_elements(By.CSS_SELECTOR, 'div[class*="message-out"]')
            
            # Match by content (last 50 chars for uniqueness)
            search_text = message_content[-50:] if len(message_content) > 50 else message_content
            
            for message in reversed(messages):  # Start from most recent
                try:
                    text_element = message.find_element(By.CSS_SELECTOR, 'span[class*="selectable-text"]')
                    if search_text in text_element.text:
                        return message
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding message element: {e}")
            return None
    
    def detect_status_icon(self, message_element):
        """Detect status icon using Selenium selectors"""
        try:
            # Look for status indicators
            status_elements = message_element.find_elements(By.CSS_SELECTOR, 'span[data-icon]')
            
            for element in status_elements:
                icon_type = element.get_attribute('data-icon')
                
                if 'double-check' in icon_type:
                    # Check if blue (read) or gray (delivered)
                    color = element.value_of_css_property('color')
                    if 'blue' in color or 'rgb(53, 168, 253)' in color:
                        return 'read'
                    else:
                        return 'delivered'
                elif 'check' in icon_type:
                    return 'sent'
                elif 'clock' in icon_type:
                    return 'pending'
            
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"Error detecting status icon: {e}")
            return 'unknown'
    
    def update_message_status(self, message_id, status):
        """Update message status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update status
            cursor.execute('UPDATE messages SET status = ? WHERE id = ?', (status, message_id))
            
            # Update delivery/read receipts
            if status == 'delivered':
                cursor.execute('UPDATE messages SET delivered = 1 WHERE id = ?', (message_id,))
            elif status == 'read':
                cursor.execute('UPDATE messages SET delivered = 1, read_receipt = 1 WHERE id = ?', (message_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Updated message {message_id} status to {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating message status: {e}")
    
    def batch_check_status(self, contact_messages):
        """Check status for multiple messages efficiently"""
        results = []
        
        # Group messages by contact to minimize navigation
        messages_by_contact = {}
        for msg in contact_messages:
            contact = msg['contact']
            if contact not in messages_by_contact:
                messages_by_contact[contact] = []
            messages_by_contact[contact].append(msg)
        
        # Process each contact
        for contact, messages in messages_by_contact.items():
            if self.navigate_to_contact(contact):
                for msg in messages:
                    status = self.check_message_status_quick(msg['id'])
                    results.append({
                        'message_id': msg['id'],
                        'contact': contact,
                        'status': status
                    })
                    time.sleep(0.5)  # Small delay between checks
        
        return results
    
    def check_message_status_quick(self, message_id):
        """Quick status check without navigation (assumes already in chat)"""
        try:
            message_element = self.find_message_element(message_id)
            if message_element:
                status = self.detect_status_icon(message_element)
                self.update_message_status(message_id, status)
                return status
            return 'not_found'
        except Exception as e:
            self.logger.error(f"Error in quick status check: {e}")
            return 'error'
    
    def monitor_real_time_status(self, message_id, timeout=300):
        """Monitor message status in real-time until delivered/read"""
        start_time = time.time()
        last_status = 'sent'
        
        while time.time() - start_time < timeout:
            current_status = self.check_message_status_quick(message_id)
            
            if current_status != last_status:
                self.logger.info(f"Message {message_id} status changed: {last_status} -> {current_status}")
                last_status = current_status
                
                # Trigger events based on status change
                self.trigger_status_event(message_id, current_status)
            
            if current_status in ['delivered', 'read', 'failed']:
                break
            
            time.sleep(5)  # Check every 5 seconds
        
        return last_status
    
    def trigger_status_event(self, message_id, status):
        """Trigger events based on status changes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get message details
            cursor.execute('SELECT contact, message FROM messages WHERE id = ?', (message_id,))
            message_data = cursor.fetchone()
            
            if message_data:
                contact, message = message_data
                
                # Log event
                cursor.execute('''
                    INSERT INTO message_events (message_id, event_type, event_data, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (message_id, f'status_changed_to_{status}', json.dumps({'status': status}), datetime.now()))
                
                # Trigger specific actions based on status
                if status == 'read':
                    # Update contact's last read time
                    cursor.execute('''
                        UPDATE contacts SET last_read_time = ? WHERE phone = ?
                    ''', (datetime.now(), contact))
                elif status == 'failed':
                    # Schedule retry
                    cursor.execute('''
                        INSERT INTO retry_queue (message_id, contact, message, retry_count, next_retry)
                        VALUES (?, ?, ?, 1, ?)
                    ''', (message_id, contact, message, datetime.now() + timedelta(minutes=5)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error triggering status event: {e}")
    
    def generate_delivery_report(self, start_date=None, end_date=None):
        """Generate comprehensive delivery report"""
        conn = sqlite3.connect(self.db_path)
        
        # Base query with optional date filtering
        query = '''
            SELECT 
                status,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
            FROM messages
        '''
        
        params = []
        if start_date and end_date:
            query += ' WHERE sent_time BETWEEN ? AND ?'
            params = [start_date, end_date]
        
        query += ' GROUP BY status'
        
        # Get status distribution
        status_dist = pd.read_sql_query(query, conn, params=params)
        
        # Get delivery performance by time
        time_query = '''
            SELECT 
                strftime('%H', sent_time) as hour,
                COUNT(CASE WHEN delivered = 1 THEN 1 END) * 100.0 / COUNT(*) as delivery_rate,
                COUNT(CASE WHEN read_receipt = 1 THEN 1 END) * 100.0 / COUNT(*) as read_rate
            FROM messages
            GROUP BY hour
            ORDER BY hour
        '''
        
        time_performance = pd.read_sql_query(time_query, conn)
        
        # Get contact-wise delivery stats
        contact_query = '''
            SELECT 
                contact,
                COUNT(*) as total_messages,
                COUNT(CASE WHEN delivered = 1 THEN 1 END) as delivered,
                COUNT(CASE WHEN read_receipt = 1 THEN 1 END) as read,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM messages
            GROUP BY contact
            ORDER BY total_messages DESC
            LIMIT 20
        '''
        
        contact_stats = pd.read_sql_query(contact_query, conn)
        
        conn.close()
        
        return {
            'status_distribution': status_dist,
            'time_performance': time_performance,
            'contact_stats': contact_stats
        }
    
    def get_failed_messages(self, retry_eligible=True):
        """Get list of failed messages"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                m.id,
                m.contact,
                m.message,
                m.sent_time,
                m.status,
                c.name
            FROM messages m
            LEFT JOIN contacts c ON m.contact = c.phone
            WHERE m.status = 'failed'
        '''
        
        if retry_eligible:
            query += '''
                AND NOT EXISTS (
                    SELECT 1 FROM retry_queue r 
                    WHERE r.message_id = m.id AND r.retry_count >= 3
                )
            '''
        
        failed_messages = pd.read_sql_query(query, conn)
        conn.close()
        
        return failed_messages
    
    def analyze_delivery_patterns(self):
        """Analyze delivery patterns for optimization"""
        conn = sqlite3.connect(self.db_path)
        
        # Best delivery times
        best_times_query = '''
            SELECT 
                strftime('%H', sent_time) as hour,
                strftime('%w', sent_time) as day_of_week,
                COUNT(CASE WHEN delivered = 1 THEN 1 END) * 100.0 / COUNT(*) as delivery_rate,
                COUNT(CASE WHEN read_receipt = 1 THEN 1 END) * 100.0 / COUNT(CASE WHEN delivered = 1 THEN 1 END) as read_rate_if_delivered
            FROM messages
            GROUP BY hour, day_of_week
            HAVING COUNT(*) > 10
            ORDER BY delivery_rate DESC, read_rate_if_delivered DESC
        '''
        
        best_times = pd.read_sql_query(best_times_query, conn)
        
        # Contact responsiveness patterns
        responsiveness_query = '''
            SELECT 
                c.phone,
                c.name,
                COUNT(m.id) as total_messages,
                AVG(CASE WHEN m.delivered = 1 THEN 1.0 ELSE 0.0 END) as avg_delivery_rate,
                AVG(CASE WHEN m.read_receipt = 1 THEN 1.0 ELSE 0.0 END) as avg_read_rate,
                AVG(CASE WHEN m.response IS NOT NULL THEN 1.0 ELSE 0.0 END) as avg_response_rate
            FROM contacts c
            LEFT JOIN messages m ON c.phone = m.contact
            GROUP BY c.phone, c.name
            HAVING COUNT(m.id) > 5
            ORDER BY avg_response_rate DESC
        '''
        
        responsiveness = pd.read_sql_query(responsiveness_query, conn)
        
        conn.close()
        
        # Generate insights
        insights = []
        
        # Best time insights
        best_hour = best_times.loc[best_times['delivery_rate'].idxmax()]
        insights.append(f"Best delivery time: {best_hour['hour']}:00 (Delivery rate: {best_hour['delivery_rate']:.1f}%)")
        
        # Day of week insights
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        best_day = best_times.groupby('day_of_week')['delivery_rate'].mean().idxmax()
        insights.append(f"Best day for messaging: {day_names[int(best_day)]}")
        
        # Responsiveness insights
        high_responders = responsiveness[responsiveness['avg_response_rate'] > 0.5]
        insights.append(f"High-responsive contacts: {len(high_responders)} ({len(high_responders)/len(responsiveness)*100:.1f}%)")
        
        return {
            'best_times': best_times,
            'responsiveness': responsiveness,
            'insights': insights
        }
    
    def export_delivery_report(self, filename='delivery_report.xlsx'):
        """Export delivery report to Excel"""
        report_data = self.generate_delivery_report()
        pattern_data = self.analyze_delivery_patterns()
        
        with pd.ExcelWriter(filename) as writer:
            report_data['status_distribution'].to_excel(writer, sheet_name='Status Distribution', index=False)
            report_data['time_performance'].to_excel(writer, sheet_name='Time Performance', index=False)
            report_data['contact_stats'].to_excel(writer, sheet_name='Contact Stats', index=False)
            pattern_data['best_times'].to_excel(writer, sheet_name='Best Times', index=False)
            pattern_data['responsiveness'].to_excel(writer, sheet_name='Contact Responsiveness', index=False)
            
            # Add insights sheet
            insights_df = pd.DataFrame({'Insights': pattern_data['insights']})
            insights_df.to_excel(writer, sheet_name='Insights', index=False)
        
        self.logger.info(f"Delivery report exported to {filename}")
        return filename