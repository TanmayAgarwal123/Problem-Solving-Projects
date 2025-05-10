import os
import shutil
import datetime
import time

def create_folders(directory, organize_by):
    """Create folders based on organization method"""
    if organize_by == "type":
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
        
        return folders
    
    elif organize_by == "date":
        # No predefined folders needed for date-based organization
        # We'll create them dynamically
        return {}
    
    elif organize_by == "size":
        folders = {
            'Small (0-1MB)': (0, 1 * 1024 * 1024),
            'Medium (1-10MB)': (1 * 1024 * 1024, 10 * 1024 * 1024),
            'Large (10-100MB)': (10 * 1024 * 1024, 100 * 1024 * 1024),
            'Very Large (100MB+)': (100 * 1024 * 1024, float('inf'))
        }
        
        # Create folders if they don't exist
        for folder_name in folders:
            folder_path = os.path.join(directory, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
        
        return folders

def get_file_category_by_type(file_ext, folders):
    """Determine which category a file belongs to based on its extension"""
    for folder, extensions in folders.items():
        if file_ext in extensions:
            return folder
    return 'Others'

def get_file_category_by_date(file_path):
    """Determine date-based folder structure for a file"""
    # Get file modification time
    mod_time = os.path.getmtime(file_path)
    date = datetime.datetime.fromtimestamp(mod_time)
    
    # Create folder structure: Year/Month
    year = str(date.year)
    month = date.strftime("%B")  # Full month name
    
    return os.path.join(year, month)

def get_file_category_by_size(file_path, folders):
    """Determine which size category a file belongs to"""
    file_size = os.path.getsize(file_path)
    
    for folder, (min_size, max_size) in folders.items():
        if min_size <= file_size < max_size:
            return folder
    
    return 'Others'

def organize_files(directory, folders, organize_by):
    """Organize files based on the chosen method"""
    # Get all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    for file in files:
        # Skip the script file itself
        if file == os.path.basename(__file__):
            continue
        
        source = os.path.join(directory, file)
        
        # Determine target folder based on organization method
        if organize_by == "type":
            file_ext = os.path.splitext(file)[1].lower()
            target_folder = get_file_category_by_type(file_ext, folders)
            destination_folder = os.path.join(directory, target_folder)
        
        elif organize_by == "date":
            target_folder = get_file_category_by_date(source)
            destination_folder = os.path.join(directory, target_folder)
            # Create year/month folders if they don't exist
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
        
        elif organize_by == "size":
            target_folder = get_file_category_by_size(source, folders)
            destination_folder = os.path.join(directory, target_folder)
        
        # Final destination path
        destination = os.path.join(destination_folder, file)
        
        # Handle duplicate files
        if os.path.exists(destination):
            # Add timestamp to filename
            filename, extension = os.path.splitext(file)
            new_filename = f"{filename}_{int(time.time())}{extension}"
            destination = os.path.join(destination_folder, new_filename)
        
        # Move the file
        try:
            shutil.move(source, destination)
            print(f"Moved: {file} to {target_folder}")
        except Exception as e:
            print(f"Error moving {file}: {e}")

def main():
    # Get the directory to organize (default is Downloads folder)
    user_home = os.path.expanduser("~")
    default_directory = os.path.join(user_home, "Downloads")
    
    print(f"Default directory to organize: {default_directory}")
    custom_dir = input("Enter a custom directory to organize or press Enter to use default: ")
    
    directory_to_organize = custom_dir if custom_dir else default_directory
    
    # Check if directory exists
    if not os.path.exists(directory_to_organize):
        print(f"Directory {directory_to_organize} does not exist!")
        return
    
    # Ask for organization method
    print("\nHow would you like to organize files?")
    print("1. By file type (images, documents, etc.)")
    print("2. By date (year/month)")
    print("3. By file size")
    
    choice = input("Enter your choice (1, 2, or 3): ")
    
    organize_by = "type"  # Default
    if choice == "2":
        organize_by = "date"
    elif choice == "3":
        organize_by = "size"
    
    print(f"\nOrganizing files in: {directory_to_organize} by {organize_by}")
    
    # Create folders and organize files
    folders = create_folders(directory_to_organize, organize_by)
    organize_files(directory_to_organize, folders, organize_by)
    
    print("File organization complete!")

if __name__ == "__main__":
    main()