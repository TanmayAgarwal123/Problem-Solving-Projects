import os
import hashlib
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class DuplicateDetector:
    def __init__(self):
        self.hash_cache = {}
    
    def find_duplicates(self, folder_path):
        """Find duplicate files in a folder"""
        duplicates = defaultdict(list)
        
        for root, _, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    file_hash = self._get_file_hash(file_path)
                    duplicates[file_hash].append(file_path)
                except Exception as e:
                    logger.error(f"Error hashing {file_path}: {e}")
        
        # Filter out non-duplicates
        return {
            hash_value: paths 
            for hash_value, paths in duplicates.items() 
            if len(paths) > 1
        }
    
    def _get_file_hash(self, file_path):
        """Generate MD5 hash for a file"""
        if file_path in self.hash_cache:
            return self.hash_cache[file_path]
        
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        
        file_hash = hasher.hexdigest()
        self.hash_cache[file_path] = file_hash
        return file_hash
    
    def get_file_similarity(self, file1, file2):
        """Calculate similarity between two files"""
        # For now, just check if they're identical
        try:
            return 1.0 if self._get_file_hash(file1) == self._get_file_hash(file2) else 0.0
        except:
            return 0.0