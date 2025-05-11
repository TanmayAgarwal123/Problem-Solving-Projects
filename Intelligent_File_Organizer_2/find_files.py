import os
import fnmatch

def find_files(root_path, pattern="*"):
    """Find files matching pattern"""
    matches = []
    for root, dirs, files in os.walk(root_path):
        for filename in fnmatch.filter(files, pattern):
            matches.append(os.path.join(root, filename))
    return matches

if __name__ == "__main__":
    search_path = input("Enter the folder to search in: ")
    file_pattern = input("Enter file pattern to search (e.g., *.jpg, document*, *): ")
    
    if not file_pattern:
        file_pattern = "*"
    
    print(f"\nSearching for '{file_pattern}' in {search_path}...")
    found_files = find_files(search_path, file_pattern)
    
    if found_files:
        print(f"\nFound {len(found_files)} files:")
        for file in found_files:
            print(f"  {file}")
    else:
        print("No files found matching the pattern.")