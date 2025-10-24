# OCR Model Training Guide

This guide explains how to train and use the CNN-based OCR model for improved character recognition accuracy.

## Prerequisites

1. **Kaggle API Credentials**
   - Go to https://www.kaggle.com/settings
   - Scroll to "API" section
   - Click "Create New API Token"
   - This downloads `kaggle.json`
   - Place it in the appropriate directory:
     - **Windows**: `C:\Users\<YourUsername>\.kaggle\kaggle.json`
     - **Linux/Mac**: `~/.kaggle/kaggle.json`

2. **Install Required Packages**
   ```bash
   pip install -r requirements.txt
   ```

## Training the Model

### Option 1: Run the Training Script (Recommended)

```bash
python train_ocr_model.py
```

This script will:
1. Install necessary packages (kagglehub, tensorflow, etc.)
2. Download the standard-ocr-dataset from Kaggle (~20,000 training images)
3. Preprocess images (resize to 32x32, normalize, grayscale)
4. Train a CNN model with data augmentation
5. Save the trained model as `ocr_character_model.h5`
6. Generate training history plots
7. Evaluate on test data

**Training Time**: 
- With GPU: ~5-10 minutes
- With CPU: ~30-60 minutes

**Expected Accuracy**: 95%+ on validation set

### Option 2: Manual Training Steps

If you prefer to train step-by-step or customize the training:

1. **Download the Dataset**
   ```python
   import kagglehub
   path = kagglehub.dataset_download("preatcher/standard-ocr-dataset")
   print("Dataset path:", path)
   ```

2. **Load and Preprocess Data**
   - Images are organized in folders by character (0-9, A-Z)
   - Each image is 32x32 grayscale
   - Normalize pixel values to [0, 1]

3. **Train the Model**
   - CNN architecture with 2 convolutional blocks
   - Data augmentation (rotation, shift, zoom)
   - 20 epochs with Adam optimizer
   - Categorical cross-entropy loss

4. **Save the Model**
   ```python
   model.save('ocr_character_model.h5')
   ```

## Using the Trained Model

### In Your OCR Pipeline

The trained model is automatically integrated into `ocr.py`. When you call `read_text_from_frame()`, it will:

1. **First** try the CNN model (if available)
2. **Then** fall back to traditional OCR methods (Tesseract, EasyOCR)

```python
from ocr import read_text_from_frame
import cv2

# Read an image
frame = cv2.imread('test_image.jpg')

# Extract text (CNN model will be used automatically)
text = read_text_from_frame(frame, use_cnn=True)
print(f"Detected text: {text}")
```

### Direct CNN Usage

For more control, you can use the CNN model directly:

```python
from ocr_cnn import get_cnn_recognizer
import cv2

# Get the recognizer
recognizer = get_cnn_recognizer()

# Check if model is available
if recognizer.is_available():
    # Read image
    img = cv2.imread('character.png')
    
    # Predict single character
    char = recognizer.predict_character(img, confidence_threshold=0.6)
    print(f"Predicted character: {char}")
    
    # Or recognize text from region
    text = recognizer.segment_and_recognize(img)
    print(f"Recognized text: {text}")
```

### With Bounding Boxes

If you have detected text regions (bounding boxes):

```python
from ocr_cnn import read_text_with_cnn

# boxes should be a list of dicts with 'xyxy' coordinates
boxes = [
    {'xyxy': [10, 20, 50, 60]},
    {'xyxy': [60, 20, 100, 60]},
]

text = read_text_with_cnn(frame, boxes=boxes, confidence_threshold=0.6)
print(f"Text from boxes: {text}")
```

## Model Details

### Architecture
```
Input: 32x32x1 (grayscale image)
├── Conv2D (32 filters, 3x3) + ReLU + BatchNorm + MaxPool + Dropout(0.3)
├── Conv2D (64 filters, 3x3) + ReLU + BatchNorm + MaxPool + Dropout(0.3)
├── Flatten
├── Dense (128 units) + ReLU + Dropout(0.5)
└── Dense (36 units) + Softmax
Output: 36 classes (0-9, A-Z)
```

### Performance
- **Training Accuracy**: ~86-87%
- **Validation Accuracy**: ~95%
- **Test Accuracy**: ~97%
- **Inference Time**: <10ms per character (CPU)

### Character Support
- Digits: 0-9
- Uppercase Letters: A-Z
- Total: 36 classes

## Files Generated

After training, you'll have:

1. **ocr_character_model.h5** - Trained Keras model (~1.2 MB)
2. **char_mappings.npy** - Character to integer mappings
3. **training_history.png** - Training accuracy/loss plots

## Troubleshooting

### Kaggle API Issues
```
Error: Could not find kaggle.json
```
**Solution**: Ensure `kaggle.json` is in the correct directory with proper permissions.

### TensorFlow Not Found
```
Warning: TensorFlow not installed
```
**Solution**: 
```bash
pip install tensorflow
```

### Model Not Loading
```
Warning: CNN model not found
```
**Solution**: Run `train_ocr_model.py` first to train the model.

### Low Accuracy
If the model isn't performing well:
1. Train for more epochs (increase from 20 to 30-40)
2. Adjust learning rate (try 0.00005 or 0.0002)
3. Modify data augmentation parameters
4. Add more training data

## Advanced Customization

### Modify Model Architecture

Edit `train_ocr_model.py` and adjust the model definition:

```python
model = Sequential([
    # Add more layers or change parameters
    Conv2D(64, (3, 3), activation='relu', ...),  # More filters
    # Add more convolutional blocks
    # ...
])
```

### Change Image Size

```python
IMG_SIZE = (64, 64)  # Increase for better quality
```

### Adjust Training Parameters

```python
epochs = 30  # Train longer
learning_rate = 0.00005  # Fine-tune learning rate
batch_size = 64  # Larger batches
```

## Integration with Smart Glasses

The OCR module is already integrated into your Smart Glasses project. The system will automatically use the CNN model when:

1. The model file exists (`ocr_character_model.h5`)
2. TensorFlow is installed
3. `use_cnn=True` in `read_text_from_frame()` (default)

This provides better accuracy for reading:
- License plates
- Street signs
- Product labels
- Documents
- Any alphanumeric text

## Next Steps

1. ✅ Train the model: `python train_ocr_model.py`
2. ✅ Test with sample images
3. ✅ Integrate with your Smart Glasses application
4. ✅ Fine-tune based on your specific use case

## References

- Dataset: [Standard OCR Dataset on Kaggle](https://www.kaggle.com/datasets/preatcher/standard-ocr-dataset)
- TensorFlow: https://www.tensorflow.org/
- Keras: https://keras.io/

---

**Need Help?** Check the training logs or raise an issue with the error message.
