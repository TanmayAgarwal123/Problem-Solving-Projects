#!/usr/bin/env python3
"""
Simplified WhatsApp Pro Messenger - Works without Selenium
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import threading
import queue
import time
import random
from simple_whatsapp import SimpleWhatsAppAutomation
import webbrowser

class SimpleWhatsAppMessenger:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Pro Messenger - Simple Version")
        self.root.geometry("800x600")
        
        # Initialize components
        self.whatsapp = SimpleWhatsAppAutomation()
        self.message_queue = queue.Queue()
        self.contacts_list = []
        self.is_connected = False
        
        # Create UI
        self.setup_ui()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self.process_messages, daemon=True)
        self.processing_thread.start()
    
    def setup_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # WhatsApp connection status
        status_frame = ttk.LabelFrame(main_frame, text="WhatsApp Status", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Not Connected", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(status_frame, text="Connect WhatsApp", 
                   command=self.connect_whatsapp).pack(side=tk.LEFT)
        
        # Contacts section
        contacts_frame = ttk.LabelFrame(main_frame, text="Contacts", padding="10")
        contacts_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(contacts_frame, text="Import Contacts (CSV/Excel)", 
                   command=self.import_contacts).pack(side=tk.LEFT, padx=5)
        
        self.contacts_label = ttk.Label(contacts_frame, text="No contacts loaded")
        self.contacts_label.pack(side=tk.LEFT, padx=10)
        
        # Message section
        message_frame = ttk.LabelFrame(main_frame, text="Message", padding="10")
        message_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Template selection
        template_frame = ttk.Frame(message_frame)
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(template_frame, text="Template:").pack(side=tk.LEFT)
        self.template_var = tk.StringVar()
        template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, width=30)
        template_combo['values'] = ('Custom', 'Greeting', 'Follow-up', 'Promotional')
        template_combo.current(0)
        template_combo.pack(side=tk.LEFT, padx=10)
        template_combo.bind('<<ComboboxSelected>>', self.load_template)
        
        # Message text area
        self.message_text = tk.Text(message_frame, height=10, wrap=tk.WORD)
        self.message_text.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder info
        info_label = ttk.Label(message_frame, text="Use {name} for full name, {first_name} for first name")
        info_label.pack(pady=(5, 0))
        
        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Delay setting
        delay_frame = ttk.Frame(settings_frame)
        delay_frame.pack(fill=tk.X)
        
        ttk.Label(delay_frame, text="Delay between messages (seconds):").pack(side=tk.LEFT)
        self.delay_var = tk.StringVar(value="30-60")
        ttk.Entry(delay_frame, textvariable=self.delay_var, width=10).pack(side=tk.LEFT, padx=10)
        
        # Send button
        send_frame = ttk.Frame(main_frame)
        send_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.send_button = ttk.Button(send_frame, text="Send Messages", 
                                      command=self.send_messages, state=tk.DISABLED)
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(send_frame, text="Stop", command=self.stop_sending).pack(side=tk.LEFT, padx=5)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def connect_whatsapp(self):
        """Connect to WhatsApp Web"""
        try:
            webbrowser.open("https://web.whatsapp.com")
            response = messagebox.showinfo(
                "Connect WhatsApp",
                "1. WhatsApp Web will open in your browser\n"
                "2. Scan the QR code with your phone\n"
                "3. Keep the browser window open\n"
                "4. Click OK when you're logged in"
            )
            
            self.is_connected = True
            self.status_label.config(text="Connected", foreground="green")
            self.send_button.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {str(e)}")
    
    def import_contacts(self):
        """Import contacts from file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                # Convert to list of dictionaries
                self.contacts_list = df.to_dict('records')
                
                self.contacts_label.config(text=f"{len(self.contacts_list)} contacts loaded")
                messagebox.showinfo("Success", f"Imported {len(self.contacts_list)} contacts")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}")
    
    def load_template(self, event=None):
        """Load message template"""
        template = self.template_var.get()
        
        templates = {
            'Greeting': "Hi {first_name}! Hope you're having a great day. Just wanted to reach out and say hello!",
            'Follow-up': "Hi {first_name}, following up on our previous conversation. Do you have any questions?",
            'Promotional': "Hi {first_name}! We have an exclusive offer just for you. Limited time only!"
        }
        
        if template in templates:
            self.message_text.delete(1.0, tk.END)
            self.message_text.insert(1.0, templates[template])
    
    def send_messages(self):
        """Start sending messages"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to WhatsApp first")
            return
        
        if not self.contacts_list:
            messagebox.showwarning("No Contacts", "Please import contacts first")
            return
        
        message = self.message_text.get(1.0, tk.END).strip()
        if not message:
            messagebox.showwarning("No Message", "Please enter a message")
            return
        
        # Parse delay
        try:
            delay_range = self.delay_var.get()
            if '-' in delay_range:
                min_delay, max_delay = map(int, delay_range.split('-'))
            else:
                min_delay = max_delay = int(delay_range)
        except:
            min_delay = max_delay = 30
        
        # Queue messages
        for contact in self.contacts_list:
            delay = random.randint(min_delay, max_delay)
            self.message_queue.put((contact, message, delay))
        
        self.progress_var.set(f"Sending to {len(self.contacts_list)} contacts...")
    
    def stop_sending(self):
        """Stop sending messages"""
        # Clear the queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except:
                break
        self.progress_var.set("Stopped")
    
    def process_messages(self):
        """Process message queue in background"""
        while True:
            try:
                if not self.message_queue.empty():
                    contact, message, delay = self.message_queue.get()
                    
                    # Get contact details
                    phone = contact.get('Phone', contact.get('phone', ''))
                    name = contact.get('Name', contact.get('name', ''))
                    
                    if not phone:
                        continue
                    
                    # Personalize message
                    personalized = message.replace('{name}', name)
                    personalized = personalized.replace('{first_name}', 
                                                      name.split()[0] if name else '')
                    
                    # Update progress
                    self.progress_var.set(f"Sending to {name} ({phone})...")
                    
                    # Send message
                    if self.whatsapp.send_message_url(phone, personalized):
                        self.progress_var.set(f"Sent to {name}")
                    else:
                        self.progress_var.set(f"Failed to send to {name}")
                    
                    # Wait before next message
                    if not self.message_queue.empty():
                        time.sleep(delay)
                    
                    self.message_queue.task_done()
                else:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleWhatsAppMessenger()
    app.run()
