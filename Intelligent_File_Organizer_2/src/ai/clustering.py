import os
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import cv2
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class FileClustering:
    def __init__(self):
        self.text_vectorizer = TfidfVectorizer(max_features=100)
        
    def cluster_files(self, folder_path):
        """Cluster similar files in a folder"""
        files = []
        features = []
        
        # Collect files and extract features
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path)
                feature = self._extract_features(file_path)
                features.append(feature)
        
        if not features:
            return []
        
        # Normalize features
        features = np.array(features)
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Perform clustering
        clustering = DBSCAN(eps=0.5, min_samples=2).fit(features_scaled)
        
        # Group files by cluster
        clusters = {}
        for file_path, label in zip(files, clustering.labels_):
            if label == -1:  # Noise point
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(file_path)
        
        return list(clusters.values())
    
    def _extract_features(self, file_path):
        """Extract features from a file for clustering"""
        features = []
        
        # File size
        file_size = os.path.getsize(file_path)
        features.append(file_size)
        
        # File extension hash
        ext = os.path.splitext(file_path)[1].lower()
        ext_hash = hash(ext) % 1000
        features.append(ext_hash)
        
        # Content-based features
        mime_type = self._get_mime_type(file_path)
        
        if mime_type and mime_type.startswith('image/'):
            img_features = self._extract_image_features(file_path)
            features.extend(img_features)
        elif mime_type and mime_type.startswith('text/'):
            text_features = self._extract_text_features(file_path)
            features.extend(text_features)
        else:
            # Default features for other file types
            features.extend([0] * 10)
        
        return features
    
    def _extract_image_features(self, image_path):
        """Extract features from images"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return [0] * 10
            
            # Basic features
            height, width = img.shape[:2]
            aspect_ratio = width / height if height > 0 else 1
            
            # Color histogram
            hist_b = cv2.calcHist([img], [0], None, [8], [0, 256])
            hist_g = cv2.calcHist([img], [1], None, [8], [0, 256])
            hist_r = cv2.calcHist([img], [2], None, [8], [0, 256])
            
            # Flatten histograms
            features = [height, width, aspect_ratio]
            features.extend(hist_b.flatten()[:3])
            features.extend(hist_g.flatten()[:3])
            features.extend(hist_r.flatten()[:1])
            
            return features
        except:
            return [0] * 10
    
    def _extract_text_features(self, text_path):
        """Extract features from text files"""
        try:
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)
            
            # Basic features
            num_lines = content.count('\n')
            num_words = len(content.split())
            avg_word_length = np.mean([len(word) for word in content.split()]) if num_words > 0 else 0
            
            # Character frequency
            char_freq = {}
            for char in content.lower():
                if char.isalpha():
                    char_freq[char] = char_freq.get(char, 0) + 1
            
            # Top characters
            top_chars = sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            char_features = [freq for _, freq in top_chars]
            char_features.extend([0] * (5 - len(char_features)))
            
            features = [num_lines, num_words, avg_word_length]
            features.extend(char_features)
            features.extend([0] * 2)  # Padding
            
            return features
        except:
            return [0] * 10
    
    def _get_mime_type(self, file_path):
        """Get MIME type of a file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type