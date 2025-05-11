import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import sqlite3
import re
import threading
import queue
import logging
from whatsapp_automation import WhatsAppAutomation
from ai_engine import AIEngine
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from textblob import TextBlob
import schedule

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhatsAppProMessenger:
    def initialize_whatsapp(self):
        """Initialize WhatsApp Web connection"""
        try:
            self.status_bar.config(text="Initializing WhatsApp Web...")
            self.whatsapp_status.config(text="WhatsApp: Connecting...", foreground="orange")
            
            # Initialize WhatsApp automation
            self.whatsapp = WhatsAppAutomation(ai_engine=self.ai_engine)
            self.whatsapp.initialize_driver()
            
            # Login to WhatsApp
            messagebox.showinfo("WhatsApp Login", 
                               "Please scan the QR code in the Chrome window that just opened.\n"
                               "Click OK after you've successfully logged in.")
            
            if self.whatsapp.login_whatsapp():
                self.is_whatsapp_ready = True
                self.whatsapp_status.config(text="WhatsApp: Connected", foreground="green")
                self.status_bar.config(text="WhatsApp Web connected successfully")
            else:
                self.whatsapp_status.config(text="WhatsApp: Failed to connect", foreground="red")
                self.status_bar.config(text="Failed to connect to WhatsApp Web")
                
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp: {e}")
            self.whatsapp_status.config(text="WhatsApp: Error", foreground="red")
            messagebox.showerror("WhatsApp Error", 
                                f"Failed to initialize WhatsApp: {str(e)}\n"
                                "Please make sure Chrome is installed.")
    
    def reconnect_whatsapp(self):
        """Reconnect to WhatsApp Web"""
        if self.whatsapp:
            self.whatsapp.close()
        self.initialize_whatsapp()
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Pro Messenger - AI-Powered Bulk Messaging")
        self.root.geometry("1200x800")
        
        # Initialize AI models
        self.ai_engine = AIEngine()
        
        # Initialize WhatsApp automation
        self.whatsapp = None
        self.is_whatsapp_ready = False
        
        # Initialize database
        self.init_database()
        
        # Message queue for threading
        self.message_queue = queue.Queue()
        self.contacts_list = []
        
        # Initialize UI
        self.setup_ui()
        
        # Start background thread for message processing
        self.processing_thread = threading.Thread(target=self.process_messages, daemon=True)
        self.processing_thread.start()
        
        # Start scheduler thread for event-triggered messages
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Check WhatsApp connection on startup
        self.root.after(1000, self.initialize_whatsapp)
        
    def init_database(self):
        """Initialize SQLite database for message tracking"""
        self.conn = sqlite3.connect('whatsapp_pro.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT,
                message TEXT,
                status TEXT,
                sent_time TIMESTAMP,
                delivered BOOLEAN,
                read_receipt BOOLEAN,
                response TEXT,
                sentiment REAL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE,
                name TEXT,
                last_interaction TIMESTAMP,
                interaction_count INTEGER,
                sentiment_score REAL,
                preferences TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT,
                message TEXT,
                scheduled_time TIMESTAMP,
                event_trigger TEXT,
                status TEXT
            )
        ''')
        
        self.conn.commit()
    
    def setup_ui(self):
        """Create the main UI"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Message Composer
        self.compose_tab = ttk.Frame(notebook)
        notebook.add(self.compose_tab, text='Compose & Send')
        self.setup_compose_tab()
        
        # Tab 2: AI Analytics
        self.analytics_tab = ttk.Frame(notebook)
        notebook.add(self.analytics_tab, text='AI Analytics')
        self.setup_analytics_tab()
        
        # Tab 3: Schedule Manager
        self.schedule_tab = ttk.Frame(notebook)
        notebook.add(self.schedule_tab, text='Schedule Manager')
        self.setup_schedule_tab()
        
        # Tab 4: Dashboard
        self.dashboard_tab = ttk.Frame(notebook)
        notebook.add(self.dashboard_tab, text='Dashboard')
        self.setup_dashboard_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # WhatsApp status indicator
        self.whatsapp_status = ttk.Label(self.root, text="WhatsApp: Not Connected", 
                                       foreground="red", relief=tk.SUNKEN, anchor=tk.E)
        self.whatsapp_status.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_compose_tab(self):
        """Setup the compose and send tab"""
        # Contact selection frame
        contact_frame = ttk.LabelFrame(self.compose_tab, text="Contacts", padding=10)
        contact_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(contact_frame, text="Import Contacts", 
                   command=self.import_contacts).pack(side='left', padx=5)
        ttk.Button(contact_frame, text="AI Smart Select", 
                   command=self.ai_select_contacts).pack(side='left', padx=5)
        
        # Message composition frame
        message_frame = ttk.LabelFrame(self.compose_tab, text="Message Composition", padding=10)
        message_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # AI-powered message templates
        template_frame = ttk.Frame(message_frame)
        template_frame.pack(fill='x', pady=5)
        
        ttk.Label(template_frame, text="AI Templates:").pack(side='left')
        self.template_var = tk.StringVar()
        template_combo = ttk.Combobox(template_frame, textvariable=self.template_var)
        template_combo['values'] = ('Personalized Greeting', 'Follow-up', 'Promotional', 
                                    'Event Invitation', 'Customer Support')
        template_combo.pack(side='left', padx=10)
        ttk.Button(template_frame, text="Generate", 
                   command=self.generate_ai_template).pack(side='left')
        
        # Message text area
        self.message_text = tk.Text(message_frame, height=10, wrap='word')
        self.message_text.pack(fill='both', expand=True, pady=10)
        
        # AI enhancement buttons
        ai_frame = ttk.Frame(message_frame)
        ai_frame.pack(fill='x', pady=5)
        
        ttk.Button(ai_frame, text="Personalize Messages", 
                   command=self.personalize_messages).pack(side='left', padx=5)
        ttk.Button(ai_frame, text="Optimize Timing", 
                   command=self.optimize_timing).pack(side='left', padx=5)
        ttk.Button(ai_frame, text="Sentiment Check", 
                   command=self.check_sentiment).pack(side='left', padx=5)
        
        # Send options
        send_frame = ttk.Frame(self.compose_tab)
        send_frame.pack(fill='x', padx=10, pady=10)
        
        self.delay_var = tk.StringVar(value="30-60")
        ttk.Label(send_frame, text="Smart Delay (seconds):").pack(side='left')
        ttk.Entry(send_frame, textvariable=self.delay_var, width=10).pack(side='left', padx=5)
        
        # WhatsApp connection button
        ttk.Button(send_frame, text="Connect WhatsApp", 
                   command=self.reconnect_whatsapp).pack(side='right', padx=10)
        
        ttk.Button(send_frame, text="Send Now", 
                   command=self.send_messages).pack(side='left', padx=10)
        ttk.Button(send_frame, text="Schedule", 
                   command=self.schedule_messages).pack(side='left')
    
    def setup_analytics_tab(self):
        """Setup the AI analytics tab"""
        # Sentiment analysis frame
        sentiment_frame = ttk.LabelFrame(self.analytics_tab, text="Sentiment Analysis", padding=10)
        sentiment_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create matplotlib figure for sentiment chart
        self.sentiment_fig, self.sentiment_ax = plt.subplots(figsize=(6, 4))
        self.sentiment_canvas = FigureCanvasTkAgg(self.sentiment_fig, sentiment_frame)
        self.sentiment_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Response analysis frame
        response_frame = ttk.LabelFrame(self.analytics_tab, text="Response Analysis", padding=10)
        response_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.response_tree = ttk.Treeview(response_frame, 
                                          columns=('Contact', 'Response', 'Sentiment', 'AI Suggestion'),
                                          show='headings')
        self.response_tree.heading('Contact', text='Contact')
        self.response_tree.heading('Response', text='Response')
        self.response_tree.heading('Sentiment', text='Sentiment')
        self.response_tree.heading('AI Suggestion', text='AI Suggestion')
        self.response_tree.pack(fill='both', expand=True)
        
        ttk.Button(response_frame, text="Analyze Responses", 
                   command=self.analyze_responses).pack(pady=10)
    
    def setup_schedule_tab(self):
        """Setup the schedule manager tab"""
        # Event triggers frame
        trigger_frame = ttk.LabelFrame(self.schedule_tab, text="Event Triggers", padding=10)
        trigger_frame.pack(fill='x', padx=10, pady=10)
        
        self.trigger_var = tk.StringVar()
        trigger_options = ('Birthday', 'Anniversary', 'Follow-up', 'Recurring', 'Custom Event')
        ttk.Label(trigger_frame, text="Event Type:").pack(side='left')
        ttk.Combobox(trigger_frame, textvariable=self.trigger_var, 
                     values=trigger_options).pack(side='left', padx=10)
        
        # Scheduled messages list
        schedule_frame = ttk.LabelFrame(self.schedule_tab, text="Scheduled Messages", padding=10)
        schedule_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.schedule_tree = ttk.Treeview(schedule_frame, 
                                          columns=('Contact', 'Message', 'Time', 'Trigger', 'Status'),
                                          show='headings')
        self.schedule_tree.heading('Contact', text='Contact')
        self.schedule_tree.heading('Message', text='Message')
        self.schedule_tree.heading('Time', text='Scheduled Time')
        self.schedule_tree.heading('Trigger', text='Trigger')
        self.schedule_tree.heading('Status', text='Status')
        self.schedule_tree.pack(fill='both', expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(self.schedule_tab)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(control_frame, text="Add Schedule", 
                   command=self.add_schedule).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Edit", 
                   command=self.edit_schedule).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Delete", 
                   command=self.delete_schedule).pack(side='left', padx=5)
    
    def setup_dashboard_tab(self):
        """Setup the dashboard tab"""
        # Statistics frame
        stats_frame = ttk.LabelFrame(self.dashboard_tab, text="Statistics", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_labels = {}
        stats = ['Total Messages', 'Delivered', 'Read', 'Response Rate', 'Avg Sentiment']
        
        for i, stat in enumerate(stats):
            frame = ttk.Frame(stats_frame)
            frame.pack(side='left', padx=20)
            ttk.Label(frame, text=stat).pack()
            self.stats_labels[stat] = ttk.Label(frame, text="0", font=('Arial', 16, 'bold'))
            self.stats_labels[stat].pack()
        
        # Message history
        history_frame = ttk.LabelFrame(self.dashboard_tab, text="Message History", padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.history_tree = ttk.Treeview(history_frame, 
                                         columns=('Time', 'Contact', 'Message', 'Status', 'Sentiment'),
                                         show='headings')
        self.history_tree.heading('Time', text='Time')
        self.history_tree.heading('Contact', text='Contact')
        self.history_tree.heading('Message', text='Message')
        self.history_tree.heading('Status', text='Status')
        self.history_tree.heading('Sentiment', text='Sentiment')
        self.history_tree.pack(fill='both', expand=True)
        
        ttk.Button(history_frame, text="Refresh", 
                   command=self.refresh_dashboard).pack(pady=10)
    
    def import_contacts(self):
        """Import contacts from Excel file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                # Store contacts in memory
                self.contacts_list = df.to_dict('records')
                
                # Save to database
                for _, row in df.iterrows():
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO contacts (phone, name, interaction_count, sentiment_score)
                        VALUES (?, ?, 0, 0.0)
                    ''', (row['Phone'], row['Name']))
                
                self.conn.commit()
                messagebox.showinfo("Success", f"Imported {len(df)} contacts")
                self.status_bar.config(text=f"Loaded {len(df)} contacts")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import contacts: {str(e)}")
                logger.error(f"Contact import error: {e}")
    
    def ai_select_contacts(self):
        """Use AI to intelligently select contacts based on criteria"""
        # This would implement ML-based contact selection
        # For demo purposes, we'll show a simple dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("AI Contact Selection")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Select contacts based on:").pack(pady=10)
        
        criteria = ['High engagement', 'Positive sentiment', 'Recent interaction',
                    'No recent contact', 'Custom criteria']
        
        for criterion in criteria:
            ttk.Radiobutton(dialog, text=criterion, value=criterion).pack(anchor='w', padx=20)
        
        ttk.Button(dialog, text="Apply", command=dialog.destroy).pack(pady=20)
    
    def generate_ai_template(self):
        """Generate AI-powered message template"""
        template_type = self.template_var.get()
        
        # Placeholder for AI template generation
        # In a real implementation, this would use a language model
        templates = {
            'Personalized Greeting': "Hi {name}! Hope you're having a great day. Just wanted to reach out and...",
            'Follow-up': "Hi {name}, following up on our previous conversation about...",
            'Promotional': "Exclusive offer for you, {name}! Limited time discount on...",
            'Event Invitation': "You're invited, {name}! Join us for...",
            'Customer Support': "Hi {name}, we noticed you might need help with..."
        }
        
        template = templates.get(template_type, "Hi {name}!")
        self.message_text.delete(1.0, tk.END)
        self.message_text.insert(1.0, template)
    
    def personalize_messages(self):
        """Personalize messages using AI"""
        base_message = self.message_text.get(1.0, tk.END).strip()
        
        # This would use NLP to personalize messages
        # For demo, we'll show a simple name replacement
        if "{name}" in base_message:
            messagebox.showinfo("AI Personalization", 
                                "Messages will be personalized with contact names and preferences")
    
    def optimize_timing(self):
        """Use AI to optimize message timing"""
        # This would analyze past interaction data to find optimal sending times
        messagebox.showinfo("AI Timing Optimization", 
                            "Analyzing best times to send messages based on past interactions...")
    
    def check_sentiment(self):
        """Check message sentiment using AI"""
        message = self.message_text.get(1.0, tk.END).strip()
        
        if message:
            # Use TextBlob for sentiment analysis
            blob = TextBlob(message)
            sentiment = blob.sentiment.polarity
            
            if sentiment > 0.1:
                sentiment_text = "Positive"
                color = "green"
            elif sentiment < -0.1:
                sentiment_text = "Negative"
                color = "red"
            else:
                sentiment_text = "Neutral"
                color = "orange"
            
            messagebox.showinfo("Sentiment Analysis", 
                                f"Message sentiment: {sentiment_text} ({sentiment:.2f})")
    
    def send_messages(self):
        """Send messages with AI enhancements"""
        if not self.is_whatsapp_ready:
            messagebox.showwarning("WhatsApp Not Connected", 
                                   "Please connect to WhatsApp Web first by clicking 'Connect WhatsApp'")
            return
        
        message = self.message_text.get(1.0, tk.END).strip()
        delay_range = self.delay_var.get()
        
        if not message:
            messagebox.showwarning("Warning", "Please enter a message")
            return
        
        if not self.contacts_list:
            messagebox.showwarning("Warning", "No contacts loaded. Please import contacts first.")
            return
        
        # Parse delay range
        try:
            min_delay, max_delay = map(int, delay_range.split('-'))
        except:
            min_delay, max_delay = 30, 60
        
        # Confirm before sending
        response = messagebox.askyesno("Confirm Send", 
                                       f"Send message to {len(self.contacts_list)} contacts?")
        if not response:
            return
        
        # Queue messages for sending
        for contact in self.contacts_list:
            phone = contact.get('Phone', contact.get('phone', ''))
            name = contact.get('Name', contact.get('name', ''))
            
            if not phone:
                continue
                
            personalized_message = message.replace("{name}", name)
            personalized_message = personalized_message.replace("{first_name}", name.split()[0] if name else "")
            
            delay = random.randint(min_delay, max_delay)
            self.message_queue.put((phone, personalized_message, delay))
        
        self.status_bar.config(text=f"Queued {len(self.contacts_list)} messages for sending")
        messagebox.showinfo("Messages Queued", 
                           f"Started sending {len(self.contacts_list)} messages.\n"
                           "Check the dashboard for progress.")
    
    def process_messages(self):
        """Background thread to process message queue"""
        while True:
            try:
                if not self.message_queue.empty():
                    phone, message, delay = self.message_queue.get(timeout=1)
                    
                    if self.is_whatsapp_ready and self.whatsapp:
                        self.status_bar.config(text=f"Sending to {phone}...")
                        
                        # Send message using WhatsApp automation
                        success = self.whatsapp.send_message(phone, message)
                        
                        # Record in database
                        self.cursor.execute('''
                            INSERT INTO messages (contact, message, status, sent_time)
                            VALUES (?, ?, ?, ?)
                        ''', (phone, message, 'sent' if success else 'failed', datetime.now()))
                        self.conn.commit()
                        
                        # Update status
                        if success:
                            self.status_bar.config(text=f"Message sent to {phone}")
                        else:
                            self.status_bar.config(text=f"Failed to send to {phone}")
                        
                        # Apply delay before next message
                        if not self.message_queue.empty():
                            self.status_bar.config(text=f"Waiting {delay} seconds before next message...")
                            time.sleep(delay)
                    else:
                        self.status_bar.config(text="WhatsApp not connected")
                        time.sleep(5)
                    
                    self.message_queue.task_done()
                else:
                    time.sleep(1)
            except queue.Empty:
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                time.sleep(5)
    
    def schedule_messages(self):
        """Schedule messages for later sending"""
        # This would open a dialog to set schedule
        messagebox.showinfo("Schedule", "Message scheduling dialog would open here")
    
    def analyze_responses(self):
        """Analyze responses using AI"""
        # This would use NLP to analyze customer responses
        messagebox.showinfo("Response Analysis", "Analyzing customer responses with AI...")
    
    def refresh_dashboard(self):
        """Refresh dashboard statistics"""
        # Update statistics
        self.cursor.execute("SELECT COUNT(*) FROM messages")
        total = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM messages WHERE delivered = 1")
        delivered = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM messages WHERE read_receipt = 1")
        read = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM messages WHERE response IS NOT NULL")
        responses = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT AVG(sentiment) FROM messages WHERE sentiment IS NOT NULL")
        avg_sentiment = self.cursor.fetchone()[0] or 0
        
        # Update labels
        self.stats_labels['Total Messages'].config(text=str(total))
        self.stats_labels['Delivered'].config(text=str(delivered))
        self.stats_labels['Read'].config(text=str(read))
        self.stats_labels['Response Rate'].config(
            text=f"{(responses/total*100 if total > 0 else 0):.1f}%"
        )
        self.stats_labels['Avg Sentiment'].config(text=f"{avg_sentiment:.2f}")
        
        # Update history
        self.history_tree.delete(*self.history_tree.get_children())
        
        self.cursor.execute('''
            SELECT sent_time, contact, message, status, sentiment 
            FROM messages 
            ORDER BY sent_time DESC 
            LIMIT 100
        ''')
        
        for row in self.cursor.fetchall():
            self.history_tree.insert('', 'end', values=row)
    
    def add_schedule(self):
        """Add a scheduled message"""
        # This would open a dialog to add scheduled message
        messagebox.showinfo("Add Schedule", "Schedule dialog would open here")
    
    def edit_schedule(self):
        """Edit a scheduled message"""
        selected = self.schedule_tree.selection()
        if selected:
            messagebox.showinfo("Edit Schedule", "Edit dialog would open here")
    
    def delete_schedule(self):
        """Delete a scheduled message"""
        selected = self.schedule_tree.selection()
        if selected:
            if messagebox.askyesno("Confirm", "Delete selected schedule?"):
                self.schedule_tree.delete(selected)
    
    def run_scheduler(self):
        """Background thread for scheduled messages"""
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def on_closing(self):
        """Handle application closing"""
        if self.whatsapp:
            try:
                self.whatsapp.close()
            except:
                pass
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    app = WhatsAppProMessenger()
    app.run()