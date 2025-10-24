"""
Quick test script to verify OCR CNN model setup and functionality.
Run this after training the model to test it on sample images.
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_test_image(text: str, output_path: str):
    """Create a simple test image with text."""
    # Create white background
    img = Image.new('RGB', (200, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Draw text in center
    draw.text((50, 30), text, fill='black', font=font)
    
    # Save
    img.save(output_path)
    print(f"✓ Created test image: {output_path}")

def test_cnn_model():
    """Test the CNN OCR model."""
    print("=" * 60)
    print("OCR CNN Model Test")
    print("=" * 60)
    
    # Check if model exists
    model_path = 'ocr_character_model.h5'
    if not os.path.exists(model_path):
        print("\n❌ Model not found!")
        print(f"Expected location: {os.path.abspath(model_path)}")
        print("\nPlease run: python train_ocr_model.py")
        return
    
    print(f"\n✓ Model found: {model_path}")
    
    # Try to import ocr_cnn
    try:
        from ocr_cnn import get_cnn_recognizer
        print("✓ OCR CNN module imported successfully")
    except ImportError as e:
        print(f"❌ Could not import ocr_cnn: {e}")
        return
    
    # Get recognizer
    print("\n[1/3] Loading CNN recognizer...")
    recognizer = get_cnn_recognizer()
    
    if not recognizer.is_available():
        print("❌ CNN recognizer not available")
        print("Check if TensorFlow is installed: pip install tensorflow")
        return
    
    print("✓ CNN recognizer loaded successfully")
    
    # Create test images
    print("\n[2/3] Creating test images...")
    test_dir = "test_ocr_images"
    os.makedirs(test_dir, exist_ok=True)
    
    test_cases = [
        ("ABC", "abc.png"),
        ("123", "123.png"),
        ("X5Y", "x5y.png"),
        ("0", "zero.png"),
    ]
    
    for text, filename in test_cases:
        create_test_image(text, os.path.join(test_dir, filename))
    
    # Test predictions
    print("\n[3/3] Testing predictions...")
    print("-" * 60)
    
    for text, filename in test_cases:
        img_path = os.path.join(test_dir, filename)
        img = cv2.imread(img_path)
        
        if img is None:
            print(f"❌ Could not load {img_path}")
            continue
        
        # Try to recognize
        result = recognizer.segment_and_recognize(img, confidence_threshold=0.5)
        
        print(f"Image: {filename:15} | Expected: {text:10} | Got: {result:10} | Match: {'✓' if text.upper() == result.upper() else '✗'}")
    
    print("-" * 60)
    
    # Test with ocr.py integration
    print("\n[BONUS] Testing integration with ocr.py...")
    try:
        from ocr import read_text_from_frame
        
        # Test on one image
        test_img = cv2.imread(os.path.join(test_dir, "abc.png"))
        result = read_text_from_frame(test_img, use_cnn=True)
        print(f"✓ OCR integration test: '{result}'")
        
    except Exception as e:
        print(f"⚠ OCR integration test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. If tests passed: Your model is ready to use!")
    print("2. If tests failed: Check error messages above")
    print("3. Try the model in your Smart Glasses app")

if __name__ == "__main__":
    test_cnn_model()
