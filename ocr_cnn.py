"""
Enhanced OCR with trained CNN model for character recognition.
This module integrates the trained character recognition model with traditional OCR methods.
"""

import os
import cv2
import numpy as np
from typing import List, Optional
from PIL import Image

__all__ = ["CNNCharacterRecognizer", "read_text_with_cnn"]


class CNNCharacterRecognizer:
    """Character recognition using trained CNN model."""
    
    def __init__(self, model_path: str = None):
        """Initialize the CNN character recognizer.
        
        Args:
            model_path: Path to the trained .h5 model file
        """
        self.model = None
        self.char_to_int = None
        self.int_to_char = None
        self.IMG_SIZE = (32, 32)
        
        if model_path is None:
            # Try to find model in the same directory as this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(script_dir, 'ocr_character_model.h5')
        
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """Load the trained model and character mappings."""
        if not os.path.exists(self.model_path):
            print(f"Warning: CNN model not found at {self.model_path}")
            print("Please run train_ocr_model.py first to train the model.")
            return
        
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(self.model_path)
            print(f"✓ CNN OCR model loaded from {self.model_path}")
            
            # Load character mappings
            mapping_path = self.model_path.replace('.h5', '_mappings.npy')
            if not os.path.exists(mapping_path):
                # Use default mappings (0-9, A-Z)
                import string
                characters = list(string.digits + string.ascii_uppercase)
                self.char_to_int = {char: i for i, char in enumerate(characters)}
                self.int_to_char = {i: char for char, i in self.char_to_int.items()}
                print("Using default character mappings (0-9, A-Z)")
            else:
                mappings = np.load(mapping_path, allow_pickle=True).item()
                self.char_to_int = mappings['char_to_int']
                self.int_to_char = mappings['int_to_char']
                print(f"✓ Character mappings loaded from {mapping_path}")
        
        except ImportError:
            print("Warning: TensorFlow not installed. CNN OCR will not be available.")
            print("Install with: pip install tensorflow")
        except Exception as e:
            print(f"Warning: Could not load CNN model: {e}")
    
    def is_available(self) -> bool:
        """Check if the CNN model is loaded and ready to use."""
        return self.model is not None
    
    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Preprocess image for CNN prediction.
        
        Args:
            img: Input image (BGR or grayscale)
        
        Returns:
            Preprocessed image ready for prediction
        """
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Resize to model input size
        resized = cv2.resize(gray, self.IMG_SIZE, interpolation=cv2.INTER_AREA)
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # Reshape for CNN input: (1, height, width, channels)
        preprocessed = normalized.reshape(1, self.IMG_SIZE[0], self.IMG_SIZE[1], 1)
        
        return preprocessed
    
    def predict_character(self, img: np.ndarray, confidence_threshold: float = 0.5) -> Optional[str]:
        """Predict a single character from an image.
        
        Args:
            img: Input image containing a single character
            confidence_threshold: Minimum confidence to return a prediction
        
        Returns:
            Predicted character or None if confidence is too low
        """
        if not self.is_available():
            return None
        
        try:
            # Preprocess image
            preprocessed = self.preprocess_image(img)
            
            # Predict
            predictions = self.model.predict(preprocessed, verbose=0)
            
            # Get predicted class and confidence
            predicted_idx = np.argmax(predictions[0])
            confidence = predictions[0][predicted_idx]
            
            if confidence >= confidence_threshold:
                return self.int_to_char[predicted_idx]
            else:
                return None
        
        except Exception as e:
            print(f"Error during CNN prediction: {e}")
            return None
    
    def predict_from_boxes(self, frame: np.ndarray, boxes: List[dict], 
                          confidence_threshold: float = 0.5) -> List[str]:
        """Predict characters from multiple bounding boxes.
        
        Args:
            frame: Input frame
            boxes: List of bounding boxes, each with 'xyxy' coordinates
            confidence_threshold: Minimum confidence for predictions
        
        Returns:
            List of predicted characters
        """
        if not self.is_available():
            return []
        
        characters = []
        for box in boxes:
            try:
                # Extract box coordinates
                xy = box.get('xyxy') if isinstance(box, dict) else box
                x1, y1, x2, y2 = map(int, xy)
                
                # Extract crop
                crop = frame[y1:y2, x1:x2]
                
                if crop is None or crop.size == 0:
                    continue
                
                # Predict character
                char = self.predict_character(crop, confidence_threshold)
                if char:
                    characters.append(char)
            
            except Exception as e:
                print(f"Error processing box: {e}")
                continue
        
        return characters
    
    def segment_and_recognize(self, img: np.ndarray, confidence_threshold: float = 0.5) -> str:
        """Segment text region into individual characters and recognize them.
        
        This is a simple segmentation approach using contours.
        For better results, consider using specialized text detection models.
        
        Args:
            img: Input image containing text
            confidence_threshold: Minimum confidence for predictions
        
        Returns:
            Recognized text string
        """
        if not self.is_available():
            return ""
        
        try:
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Apply thresholding
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Sort contours left to right
            contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])
            
            # Recognize each character
            recognized_chars = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter out very small contours (noise)
                if w < 5 or h < 5:
                    continue
                
                # Extract character region
                char_img = gray[y:y+h, x:x+w]
                
                # Add padding
                pad = 5
                char_img = cv2.copyMakeBorder(char_img, pad, pad, pad, pad, 
                                             cv2.BORDER_CONSTANT, value=255)
                
                # Predict
                char = self.predict_character(char_img, confidence_threshold)
                if char:
                    recognized_chars.append(char)
            
            return ''.join(recognized_chars)
        
        except Exception as e:
            print(f"Error during segmentation and recognition: {e}")
            return ""


# Global instance for easy access
_cnn_recognizer = None


def get_cnn_recognizer(model_path: str = None) -> CNNCharacterRecognizer:
    """Get or create the global CNN recognizer instance.
    
    Args:
        model_path: Optional path to model file
    
    Returns:
        CNNCharacterRecognizer instance
    """
    global _cnn_recognizer
    if _cnn_recognizer is None:
        _cnn_recognizer = CNNCharacterRecognizer(model_path)
    return _cnn_recognizer


def read_text_with_cnn(frame: np.ndarray, boxes: Optional[List[dict]] = None, 
                       confidence_threshold: float = 0.5) -> str:
    """Read text from frame using CNN character recognition.
    
    Args:
        frame: Input frame
        boxes: Optional bounding boxes for text regions
        confidence_threshold: Minimum confidence for predictions
    
    Returns:
        Recognized text string
    """
    recognizer = get_cnn_recognizer()
    
    if not recognizer.is_available():
        return ""
    
    # If boxes are provided, use them
    if boxes:
        characters = recognizer.predict_from_boxes(frame, boxes, confidence_threshold)
        return ' '.join(characters) if characters else ""
    
    # Otherwise, try to segment and recognize
    return recognizer.segment_and_recognize(frame, confidence_threshold)
