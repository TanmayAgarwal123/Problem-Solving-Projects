import sys
import os
import logging
import platform
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import FileOrganizerGUI
from src.core.scheduler import ScheduleManager

def setup_logging():
    """Setup logging configuration"""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/file_organizer.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Start the scheduler service
        scheduler = ScheduleManager()
        scheduler.start()
        
        # Start the GUI
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Modern look
        
        window = FileOrganizerGUI()
        window.show()
        
        sys.exit(app.exec_())
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        if platform.system() != "Windows" and "win32com" in str(e):
            logger.info("Note: Windows Task Scheduler features are not available on this platform")
            # Continue without Windows-specific features
            app = QApplication(sys.argv)
            window = FileOrganizerGUI()
            window.show()
            sys.exit(app.exec_())
        else:
            raise

if __name__ == "__main__":
    main()