import os
import hashlib
from datetime import datetime
import mimetypes

def get_file_info(file_path):
    """Get comprehensive file information"""
    stat = os.stat(file_path)
    
    return {
        'path': file_path,
        'name': os.path.basename(file_path),
        'extension': os.path.splitext(file_path)[1].lower(),
        'size': stat.st_size,
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'mime_type': mimetypes.guess_type(file_path)[0]
    }

def generate_hash(file_path, algorithm='md5'):
    """Generate file hash for duplicate detection"""
    hash_algo = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_algo.update(chunk)
    
    return hash_algo.hexdigest()

def format_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"