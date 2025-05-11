import os
import shutil
import json
from datetime import datetime
from pathlib import Path
import logging
from ..ai.classifier import FileClassifier
from ..ai.clustering import FileClustering
from ..utils.file_utils import get_file_info, generate_hash
from ..utils.analytics import Analytics

logger = logging.getLogger(__name__)

class SmartOrganizer:
    def __init__(self, config_path="config.json"):
        self.config = self._load_config(config_path)
        self.classifier = FileClassifier()
        self.clustering = FileClustering()
        self.analytics = Analytics()
        
    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        default_config = {
            "folders": {
                "documents": [".pdf", ".docx", ".doc", ".txt", ".odt", ".rtf"],
                "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
                "videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
                "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
                "archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
                "code": [".py", ".js", ".html", ".css", ".cpp", ".java", ".c", ".h", ".php", ".rb", ".go"],
                "spreadsheets": [".xlsx", ".xls", ".csv", ".ods"],
                "presentations": [".pptx", ".ppt", ".odp"],
                "ebooks": [".epub", ".mobi", ".azw3"],
                "executables": [".exe", ".msi", ".deb", ".rpm", ".app"]
            },
            "rules": {
                "use_ai_classification": False,
                "use_content_analysis": False,
                "min_duplicate_similarity": 0.85,
                "cluster_similar_files": False,
                "preserve_folder_structure": True,
                "organization_mode": "type"
            },
            "size_categories": {
                "small": {
                    "max_size_mb": 1,
                    "folder_name": "small_files"
                },
                "medium": {
                    "max_size_mb": 10,
                    "folder_name": "medium_files"
                },
                "large": {
                    "max_size_mb": 100,
                    "folder_name": "large_files"
                },
                "very_large": {
                    "folder_name": "very_large_files"
                }
            }
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Merge loaded config with defaults
                for key in default_config:
                    if key in loaded_config:
                        if isinstance(default_config[key], dict):
                            default_config[key].update(loaded_config[key])
                        else:
                            default_config[key] = loaded_config[key]
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Error loading config file: {e}. Using defaults.")
        else:
            # Create config file with defaults
            try:
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default configuration file: {config_path}")
            except Exception as e:
                logger.warning(f"Could not create config file: {e}")
        
        return default_config
    
    def organize_folder(self, source_folder, destination_folder=None, **kwargs):
        """Organize files with various modes and options"""
        # Get parameters from kwargs with defaults
        organization_mode = kwargs.get('organization_mode', 'type')
        preserve_structure = kwargs.get('preserve_structure', True)
        include_subfolders = kwargs.get('include_subfolders', False)
        
        if not destination_folder:
            destination_folder = source_folder
            
        logger.info(f"Starting organization of {source_folder} with mode: {organization_mode}")
        stats = {"moved": 0, "duplicates": 0, "errors": 0, "preserved": 0}
        
        # Get all files to process based on settings
        files_to_process = self._get_files_to_process(source_folder, include_subfolders, preserve_structure)
        
        # Process files based on organization mode
        for file_info in files_to_process:
            try:
                file_path = file_info['path']
                
                # Skip if file is in a preserved folder
                if file_info.get('preserve', False):
                    stats["preserved"] += 1
                    continue
                
                # Determine destination based on organization mode
                if organization_mode == "type":
                    dest_folder = self._organize_by_type(file_path, destination_folder)
                elif organization_mode == "date":
                    dest_folder = self._organize_by_date(file_path, destination_folder)
                elif organization_mode == "size":
                    dest_folder = self._organize_by_size(file_path, destination_folder)
                elif organization_mode == "ai":
                    dest_folder = self._organize_by_ai(file_path, destination_folder)
                else:
                    dest_folder = destination_folder
                
                # Create destination directory
                os.makedirs(dest_folder, exist_ok=True)
                
                # Handle duplicates
                dest_path = os.path.join(dest_folder, os.path.basename(file_path))
                if os.path.exists(dest_path):
                    if self._handle_duplicate(file_path, dest_path):
                        stats["duplicates"] += 1
                        continue
                
                # Move file
                shutil.move(file_path, dest_path)
                stats["moved"] += 1
                
                # Update analytics
                file_info = get_file_info(dest_path)
                self.analytics.log_organization(file_info, os.path.basename(dest_folder))
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                stats["errors"] += 1
        
        logger.info(f"Organization complete. Stats: {stats}")
        return stats
    
    def _get_files_to_process(self, source_folder, include_subfolders, preserve_structure):
        """Get list of files to process based on settings"""
        files_to_process = []
        
        if include_subfolders:
            for root, dirs, files in os.walk(source_folder):
                # Check if this is a subfolder that should be preserved
                relative_path = os.path.relpath(root, source_folder)
                should_preserve = preserve_structure and relative_path != "."
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_info = {
                        'path': file_path,
                        'preserve': should_preserve,
                        'relative_dir': relative_path if should_preserve else None
                    }
                    files_to_process.append(file_info)
        else:
            # Only process files in the root directory
            for item in os.listdir(source_folder):
                item_path = os.path.join(source_folder, item)
                if os.path.isfile(item_path):
                    file_info = {
                        'path': item_path,
                        'preserve': False,
                        'relative_dir': None
                    }
                    files_to_process.append(file_info)
        
        return files_to_process
    
    def _organize_by_type(self, file_path, destination_folder):
        """Organize by file type/extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Check predefined categories
        for category, extensions in self.config["folders"].items():
            if ext in extensions:
                return os.path.join(destination_folder, category)
        
        # Default category
        if ext:
            return os.path.join(destination_folder, f"{ext[1:]}_files")
        else:
            return os.path.join(destination_folder, "no_extension")
    
    def _organize_by_date(self, file_path, destination_folder):
        """Organize by file modification date"""
        file_stat = os.stat(file_path)
        mod_time = datetime.fromtimestamp(file_stat.st_mtime)
        
        # Create year/month structure
        year_folder = os.path.join(destination_folder, str(mod_time.year))
        month_folder = os.path.join(year_folder, f"{mod_time.month:02d}-{mod_time.strftime('%B')}")
        
        return month_folder
    
    def _organize_by_size(self, file_path, destination_folder):
        """Organize by file size"""
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        size_categories = self.config.get("size_categories", {})
        
        if file_size_mb < size_categories.get("small", {}).get("max_size_mb", 1):
            folder_name = size_categories.get("small", {}).get("folder_name", "small_files")
        elif file_size_mb < size_categories.get("medium", {}).get("max_size_mb", 10):
            folder_name = size_categories.get("medium", {}).get("folder_name", "medium_files")
        elif file_size_mb < size_categories.get("large", {}).get("max_size_mb", 100):
            folder_name = size_categories.get("large", {}).get("folder_name", "large_files")
        else:
            folder_name = size_categories.get("very_large", {}).get("folder_name", "very_large_files")
        
        return os.path.join(destination_folder, folder_name)
    
    def _organize_by_ai(self, file_path, destination_folder):
        """Use AI classification"""
        category = self.classifier.classify_file(file_path)
        
        if self.config["rules"]["use_content_analysis"]:
            category = self.classifier.analyze_content(file_path, category)
        
        return os.path.join(destination_folder, category)
    
    def _handle_duplicate(self, source_file, existing_file):
        """Handle duplicate files"""
        # Check if files are identical
        if generate_hash(source_file) == generate_hash(existing_file):
            logger.info(f"Exact duplicate found: {source_file}")
            os.remove(source_file)
            return True
        
        # Rename if not duplicate
        base, ext = os.path.splitext(existing_file)
        counter = 1
        new_path = existing_file
        while os.path.exists(new_path):
            new_path = f"{base}_{counter}{ext}"
            counter += 1
        
        return False