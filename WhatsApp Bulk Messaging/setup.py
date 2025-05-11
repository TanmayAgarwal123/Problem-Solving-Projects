#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version: {sys.version}")

def install_requirements():
    """Install required Python packages"""
    print("\nInstalling required packages...")
    
    # Upgrade pip first
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    print("✓ All packages installed successfully")

def download_nltk_data():
    """Download required NLTK data"""
    print("\nDownloading NLTK data...")
    import nltk
    
    nltk_packages = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
    for package in nltk_packages:
        try:
            nltk.download(package, quiet=True)
            print(f"✓ Downloaded {package}")
        except Exception as e:
            print(f"Warning: Failed to download {package}: {e}")

def setup_chrome_driver():
    """Setup Chrome WebDriver"""
    print("\nSetting up Chrome WebDriver...")
    
    system = platform.system()
    
    if system == "Windows":
        driver_name = "chromedriver.exe"
    else:
        driver_name = "chromedriver"
    
    # Check if chromedriver exists
    if not shutil.which(driver_name):
        print("ChromeDriver not found. Please install it manually:")
        print("1. Download from: https://chromedriver.chromium.org/downloads")
        print("2. Make sure it matches your Chrome version")
        print("3. Add it to your system PATH")
        return False
    
    print("✓ ChromeDriver found")
    return True

def setup_tesseract():
    """Setup Tesseract OCR"""
    print("\nChecking Tesseract OCR...")
    
    if not shutil.which("tesseract"):
        print("Tesseract OCR not found. Please install it:")
        
        system = platform.system()
        if system == "Windows":
            print("Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        elif system == "Darwin":  # macOS
            print("macOS: brew install tesseract")
        else:  # Linux
            print("Linux: sudo apt-get install tesseract-ocr")
        
        return False
    
    print("✓ Tesseract OCR found")
    return True

def create_directory_structure():
    """Create necessary directories"""
    print("\nCreating directory structure...")
    
    directories = [
        "logs",
        "data",
        "exports",
        "media",
        "chrome_data",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created {directory}/")

def initialize_database():
    """Initialize the SQLite database"""
    print("\nInitializing database...")
    
    from main import WhatsAppProMessenger
    from event_trigger import EventTriggerSystem
    from follow_up_system import SmartFollowUpSystem
    
    # Initialize main database
    app = WhatsAppProMessenger()
    app.init_database()
    
    # Initialize event triggers
    event_system = EventTriggerSystem()
    event_system.create_default_triggers()
    
    # Initialize follow-up rules
    follow_up_system = SmartFollowUpSystem()
    follow_up_system.create_follow_up_rules()
    
    print("✓ Database initialized successfully")

def create_config_file():
    """Create a configuration file"""
    print("\nCreating configuration file...")
    
    config_content = """# WhatsApp Pro Messenger Configuration

# AI/ML Settings
AI_ENABLED = true
SENTIMENT_ANALYSIS = true
AUTO_PERSONALIZATION = true
SMART_TIMING = true

# Messaging Settings
MIN_DELAY_SECONDS = 30
MAX_DELAY_SECONDS = 60
MAX_RETRIES = 3
BATCH_SIZE = 50

# Follow-up Settings
FOLLOW_UP_ENABLED = true
NO_RESPONSE_HOURS = 24
MAX_FOLLOW_UPS = 2

# Event Triggers
EVENT_TRIGGERS_ENABLED = true
BIRTHDAY_MESSAGES = true
RE_ENGAGEMENT_DAYS = 30

# Delivery Confirmation
DELIVERY_TRACKING = true
READ_RECEIPT_TRACKING = true
REAL_TIME_MONITORING = false

# Export Settings
AUTO_EXPORT_REPORTS = true
EXPORT_FORMAT = excel
EXPORT_FREQUENCY = weekly

# Logging
LOG_LEVEL = INFO
LOG_FILE = logs/whatsapp_pro.log

# Database
DB_PATH = whatsapp_pro.db
BACKUP_ENABLED = true
BACKUP_FREQUENCY = daily
"""
    
    with open("config.ini", "w") as f:
        f.write(config_content)
    
    print("✓ Configuration file created")

def create_example_files():
    """Create example files for testing"""
    print("\nCreating example files...")
    
    # Example contacts CSV
    contacts_csv = """Name,Phone
John Doe,+1234567890
Jane Smith,+1234567891
Bob Johnson,+1234567892
Alice Brown,+1234567893
Mike Wilson,+1234567894
"""
    
    with open("data/example_contacts.csv", "w") as f:
        f.write(contacts_csv)
    
    # Example message templates
    templates = {
        "welcome": "Hi {first_name}! Welcome to our service. We're excited to have you on board!",
        "follow_up": "Hi {first_name}, just following up on my previous message. Did you have a chance to check it out?",
        "birthday": "Happy Birthday {first_name}! 🎉 Wishing you a wonderful day filled with joy!",
        "promotional": "Hi {first_name}, we have an exclusive offer just for you! Limited time only.",
        "re_engagement": "Hi {first_name}, we miss you! Here's a special offer to welcome you back."
    }
    
    import json
    with open("data/message_templates.json", "w") as f:
        json.dump(templates, f, indent=2)
    
    print("✓ Example files created")

def run_tests():
    """Run basic tests to ensure everything is working"""
    print("\nRunning tests...")
    
    try:
        # Test imports
        import cv2
        import selenium
        import transformers
        import torch
        
        # Test AI engine
        from ai_engine import AIEngine
        ai = AIEngine()
        sentiment = ai.analyze_sentiment("This is a great product!")
        print(f"✓ AI Engine test passed. Sentiment: {sentiment}")
        
        print("✓ All tests passed")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=== WhatsApp Pro Messenger Setup ===\n")
    
    # Check Python version
    check_python_version()
    
    # Install requirements
    try:
        install_requirements()
    except Exception as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)
    
    # Download NLTK data
    try:
        download_nltk_data()
    except Exception as e:
        print(f"Warning: NLTK data download failed: {e}")
    
    # Setup external dependencies
    chrome_ok = setup_chrome_driver()
    tesseract_ok = setup_tesseract()
    
    if not chrome_ok or not tesseract_ok:
        print("\nWarning: Some external dependencies are missing.")
        print("The application may not work properly without them.")
    
    # Create directory structure
    create_directory_structure()
    
    # Initialize database
    try:
        initialize_database()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    
    # Create configuration file
    create_config_file()
    
    # Create example files
    create_example_files()
    
    # Run tests
    tests_passed = run_tests()
    
    print("\n=== Setup Complete ===")
    if tests_passed:
        print("✓ WhatsApp Pro Messenger is ready to use!")
        print("\nTo start the application:")
        print("  python main.py")
        print("\nFor documentation, see README.md")
    else:
        print("⚠ Setup completed with warnings.")
        print("Some features may not work properly.")
        print("Please check the error messages above.")
    
    print("\nImportant Notes:")
    print("1. Make sure Chrome browser is installed")
    print("2. First run will require WhatsApp QR code scanning")
    print("3. Check config.ini for customization options")
    print("4. See data/ folder for example files")

if __name__ == "__main__":
    main()
