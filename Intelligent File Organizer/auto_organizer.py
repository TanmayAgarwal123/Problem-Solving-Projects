import os
import shutil
import datetime
import time
import logging

# Set up logging
logging.basicConfig(
    filename='file_organizer.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def create_folders(directory):
    """Create folders for different file types if they don't exist"""
    folders = {
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'Documents': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.rtf'],
        'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'],
        'Audio': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'Code': ['.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.php', '.rb', '.json', '.xml'],
        'Executables': ['.exe', '.msi', '.app', '.bat', '.sh'],
        'Others': []
    }
    
    # Create folders if they don't exist
    for folder_name in folders:
        folder_path = os.path.join(directory, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            logging.info(f"Created folder: {folder_path}")
    
    return folders

def organize_files(directory, folders):
    """Organize files into respective folders based on extension"""
    # Get all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    files_moved = 0
    for file in files:
        # Skip the script file itself and the log file
        if file == os.path.basename(__file__) or file == 'file_organizer.log':
            continue
            
        # Get the file extension
        file_ext = os.path.splitext(file)[1].lower()
        
        # Find which folder this file should go into
        target_folder = 'Others'  # Default folder
        for folder, extensions in folders.items():
            if file_ext in extensions:
                target_folder = folder
                break
        
        # Source and destination paths
        source = os.path.join(directory, file)
        destination = os.path.join(directory, target_folder, file)
        
        # Handle duplicate files
        if os.path.exists(destination):
            # Add timestamp to filename
            filename, extension = os.path.splitext(file)
            new_filename = f"{filename}_{int(time.time())}{extension}"
            destination = os.path.join(directory, target_folder, new_filename)
        
        # Move the file
        try:
            shutil.move(source, destination)
            logging.info(f"Moved: {file} to {target_folder}")
            files_moved += 1
        except Exception as e:
            logging.error(f"Error moving {file}: {e}")
    
    return files_moved

def main():
    # Default to Downloads folder
    user_home = os.path.expanduser("~")
    directory_to_organize = os.path.join(user_home, "Downloads")
    
    logging.info(f"Starting automatic file organization for: {directory_to_organize}")
    
    # Check if directory exists
    if not os.path.exists(directory_to_organize):
        logging.error(f"Directory {directory_to_organize} does not exist!")
        return
    
    # Create folders and organize files
    folders = create_folders(directory_to_organize)
    files_moved = organize_files(directory_to_organize, folders)
    
    logging.info(f"File organization complete! {files_moved} files organized.")

if __name__ == "__main__":
    main()