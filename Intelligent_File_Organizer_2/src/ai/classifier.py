import os
import mimetypes
import tensorflow as tf
from tensorflow import keras
import numpy as np
from PIL import Image
import cv2
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Try to import structural_similarity
try:
    from skimage.metrics import structural_similarity as ssim
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False
    import warnings
    warnings.warn("skimage not available, using basic image comparison")

logger = logging.getLogger(__name__)

class FileClassifier:
    def __init__(self):
        self.image_model = self._load_image_model()
        self.text_vectorizer = TfidfVectorizer(max_features=1000)
        self._setup_nltk()
    
    def _setup_nltk(self):
        """Download required NLTK data"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            pass
    
    def _load_image_model(self):
        """Load pre-trained image classification model"""
        try:
            # Use MobileNetV2 for efficient image classification
            base_model = keras.applications.MobileNetV2(
                weights='imagenet',
                include_top=True
            )
            return base_model
        except Exception as e:
            logger.warning(f"Could not load image model: {e}")
            return None
    
    def classify_batch(self, file_paths):
        """Classify multiple files using AI"""
        classifications = []
        
        for file_path in file_paths:
            try:
                classification = self.classify_file(file_path)
                classifications.append(classification)
            except Exception as e:
                logger.error(f"Error classifying {file_path}: {e}")
                classifications.append("others")
        
        return classifications
    
    def classify_file(self, file_path):
        """Classify a single file using AI"""
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type:
            if mime_type.startswith('image/'):
                return self._classify_image(file_path)
            elif mime_type.startswith('text/'):
                return self._classify_text(file_path)
            elif mime_type.startswith('application/pdf'):
                return "documents"
            elif mime_type.startswith('video/'):
                return "videos"
            elif mime_type.startswith('audio/'):
                return "audio"
        
        # Fallback to extension-based classification
        ext = os.path.splitext(file_path)[1].lower()
        extension_map = {
            '.py': 'code',
            '.js': 'code',
            '.html': 'code',
            '.css': 'code',
            '.zip': 'archives',
            '.rar': 'archives',
            '.docx': 'documents',
            '.xlsx': 'documents'
        }
        
        return extension_map.get(ext, 'others')
    
    def _classify_image(self, image_path):
        """Classify image using deep learning"""
        if not self.image_model:
            return "images"
        
        try:
            # Load and preprocess image
            img = Image.open(image_path).convert('RGB')
            img = img.resize((224, 224))
            img_array = keras.preprocessing.image.img_to_array(img)
            img_array = keras.applications.mobilenet_v2.preprocess_input(img_array)
            img_array = np.expand_dims(img_array, axis=0)
            
            # Predict
            predictions = self.image_model.predict(img_array, verbose=0)
            decoded = keras.applications.mobilenet_v2.decode_predictions(predictions, top=3)[0]
            
            # Map ImageNet classes to our categories
            top_class = decoded[0][1].lower()
            
            if any(word in top_class for word in ['document', 'paper', 'text', 'book']):
                return "documents"
            elif any(word in top_class for word in ['diagram', 'chart', 'graph']):
                return "documents"
            elif any(word in top_class for word in ['screenshot', 'screen']):
                return "screenshots"
            else:
                return "images"
            
        except Exception as e:
            logger.warning(f"Image classification failed: {e}")
            return "images"
    
    def _classify_text(self, text_path):
        """Classify text files based on content"""
        try:
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1000 chars
            
            # Simple keyword-based classification
            if any(keyword in content.lower() for keyword in ['import', 'function', 'class', 'def', 'var']):
                return "code"
            elif any(keyword in content.lower() for keyword in ['chapter', 'section', 'introduction', 'conclusion']):
                return "documents"
            else:
                return "documents"
        except:
            return "documents"
    
    def analyze_content(self, file_path, initial_category):
        """Deep content analysis for refined classification"""
        # For now, return the initial category
        # This can be expanded with more sophisticated analysis
        return initial_category
    
    def compare_images(self, img1_path, img2_path):
        """Compare two images for similarity"""
        try:
            # Load images
            img1 = cv2.imread(img1_path)
            img2 = cv2.imread(img2_path)
            
            if img1 is None or img2 is None:
                return 0.0
            
            # Resize to same dimensions
            height = min(img1.shape[0], img2.shape[0])
            width = min(img1.shape[1], img2.shape[1])
            img1 = cv2.resize(img1, (width, height))
            img2 = cv2.resize(img2, (width, height))
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            if SSIM_AVAILABLE:
                # Calculate structural similarity
                similarity = ssim(gray1, gray2)
            else:
                # Basic similarity using histogram comparison
                hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
                hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
                similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            return similarity
        except Exception as e:
            logger.warning(f"Image comparison failed: {e}")
            return 0.0