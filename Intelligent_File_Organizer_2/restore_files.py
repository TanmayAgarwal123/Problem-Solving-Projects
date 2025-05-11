import os
import shutil
from datetime import datetime

def restore_files(organized_folder, restore_info_file="organization_log.json"):
    """
    Restore files to their original locations (if we have the log)
    or at least flatten the organized structure
    """
    print(f"Scanning {organized_folder} for organized files...")
    
    # Create a restore folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    restore_folder = f"restored_files_{timestamp}"
    os.makedirs(restore_folder, exist_ok=True)
    
    files_found = 0
    
    # Walk through all organized folders
    for root, dirs, files in os.walk(organized_folder):
        for file in files:
            source_path = os.path.join(root, file)
            
            # Create a flat structure in restore folder
            # You can modify this to recreate original structure if needed
            dest_path = os.path.join(restore_folder, file)
            
            # Handle duplicates by adding numbers
            counter = 1
            base, ext = os.path.splitext(dest_path)
            while os.path.exists(dest_path):
                dest_path = f"{base}_{counter}{ext}"
                counter += 1
            
            try:
                shutil.copy2(source_path, dest_path)
                files_found += 1
                print(f"Restored: {file}")
            except Exception as e:
                print(f"Error restoring {file}: {e}")
    
    print(f"\nRestoration complete!")
    print(f"Files found and copied: {files_found}")
    print(f"Files restored to: {restore_folder}")
    
    return restore_folder

def find_organized_folders(search_path):
    """Find folders that look like they were created by the organizer"""
    organized_folders = []
    
    # Common folder names created by the organizer
    common_names = [
        "documents", "images", "videos", "audio", "archives", "code",
        "spreadsheets", "presentations", "small_files", "medium_files",
        "large_files", "very_large_files"
    ]
    
    # Also check for year folders (date organization)
    import re
    year_pattern = re.compile(r"^\d{4}$")
    
    for item in os.listdir(search_path):
        item_path = os.path.join(search_path, item)
        if os.path.isdir(item_path):
            if item.lower() in common_names or year_pattern.match(item):
                organized_folders.append(item_path)
    
    return organized_folders

if __name__ == "__main__":
    # Specify the folder where organization was performed
    source_folder = input("Enter the folder where files were organized: ")
    
    if not os.path.exists(source_folder):
        print(f"Folder {source_folder} not found!")
    else:
        print(f"\nSearching for organized folders in: {source_folder}")
        organized_folders = find_organized_folders(source_folder)
        
        if organized_folders:
            print("\nFound organized folders:")
            for folder in organized_folders:
                print(f"  - {folder}")
            
            restore = input("\nDo you want to restore files from these folders? (y/n): ")
            if restore.lower() == 'y':
                restore_files(source_folder)
        else:
            print("No organized folders found. Your files might be in subfolders.")
            restore = input("\nDo you want to restore all files from all subfolders? (y/n): ")
            if restore.lower() == 'y':
                restore_files(source_folder)