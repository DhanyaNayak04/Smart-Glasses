"""
Train OCR Character Recognition Model using Kaggle Dataset
This script downloads the standard-ocr-dataset and trains a CNN model
to recognize alphanumeric characters (0-9, A-Z).
"""

import os
import string
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# Check for Kaggle credentials
print("=" * 60)
print("OCR Model Training Script")
print("=" * 60)

# Install required packages
print("\n[1/7] Installing required packages...")
os.system("pip install kagglehub tensorflow pandas numpy matplotlib scikit-learn Pillow")

print("\n[2/7] Importing required libraries...")
import kagglehub
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import Adam

print(f"TensorFlow version: {tf.__version__}")

# Download dataset
print("\n[3/7] Downloading Kaggle dataset...")
try:
    path = kagglehub.dataset_download("preatcher/standard-ocr-dataset")
    print(f"✓ Dataset downloaded to: {path}")
except Exception as e:
    print(f"✗ Error downloading dataset: {e}")
    print("\nPlease ensure you have:")
    print("1. Kaggle API credentials configured (~/.kaggle/kaggle.json)")
    print("2. Internet connection")
    print("\nTo set up Kaggle API:")
    print("- Go to https://www.kaggle.com/settings")
    print("- Click 'Create New API Token'")
    print("- Place kaggle.json in the appropriate directory")
    exit(1)

# Set paths
training_data_path = os.path.join(path, 'data', 'training_data')
testing_data_path = os.path.join(path, 'data', 'testing_data')

print(f"Training data path: {training_data_path}")
print(f"Testing data path: {testing_data_path}")

# Load training data
print("\n[4/7] Loading and preparing training data...")
train_folder = os.listdir(training_data_path)
data = []

for label in train_folder:
    label_path = os.path.join(training_data_path, label)
    if os.path.isdir(label_path):
        for image_name in os.listdir(label_path):
            img_path = os.path.join(label_path, image_name)
            data.append((img_path, label))

df = pd.DataFrame(data, columns=['image_path', 'label'])
print(f"✓ Loaded {len(df)} training images")
print(f"✓ Number of unique classes: {df['label'].nunique()}")

# Create character to integer mapping
characters = list(string.digits + string.ascii_uppercase)
char_to_int = {char: i for i, char in enumerate(characters)}
int_to_char = {i: char for char, i in char_to_int.items()}
num_classes = len(char_to_int)

print(f"✓ Character mapping created for {num_classes} classes: {characters}")

# Image preprocessing parameters
IMG_SIZE = (32, 32)

def load_images(df):
    """Load and preprocess images from dataframe."""
    images = []
    labels = []
    
    print("  Loading images...")
    for idx, row in df.iterrows():
        if idx % 5000 == 0:
            print(f"  Progress: {idx}/{len(df)}")
        
        image_path = row['image_path']
        label = row['label']
        
        # Convert label to integer
        label_int = char_to_int[label]
        
        # Load and preprocess image
        try:
            img = load_img(image_path, target_size=IMG_SIZE, color_mode="grayscale")
            img_array = img_to_array(img)
            img_array = img_array / 255.0  # Normalize
            
            images.append(img_array)
            labels.append(label_int)
        except Exception as e:
            print(f"  Warning: Could not load {image_path}: {e}")
            continue
    
    return np.array(images), np.array(labels)

# Load images
X_train, y_train = load_images(df)
print(f"✓ Images loaded with shape: {X_train.shape}")

# Reshape for CNN input
X_train = X_train.reshape(-1, 32, 32, 1)

# Convert labels to one-hot encoding
y_train = to_categorical(y_train, num_classes)

# Split into training and validation sets
y_int_labels = np.argmax(y_train, axis=1)
X_train, X_val, y_train_int, y_val_int = train_test_split(
    X_train, y_int_labels, test_size=0.2, stratify=y_int_labels, random_state=42
)

# Convert back to one-hot encoding
y_train = to_categorical(y_train_int, num_classes)
y_val = to_categorical(y_val_int, num_classes)

print(f"✓ Training set: {X_train.shape[0]} samples")
print(f"✓ Validation set: {X_val.shape[0]} samples")

# Build CNN model
print("\n[5/7] Building CNN model...")
model = Sequential([
    # First convolutional block
    Conv2D(32, (3, 3), activation='relu', kernel_regularizer=l2(0.001), input_shape=(32, 32, 1)),
    BatchNormalization(),
    MaxPooling2D((2, 2)),
    Dropout(0.3),
    
    # Second convolutional block
    Conv2D(64, (3, 3), activation='relu', kernel_regularizer=l2(0.001)),
    BatchNormalization(),
    MaxPooling2D((2, 2)),
    Dropout(0.3),
    
    # Fully connected layers
    Flatten(),
    Dense(128, activation='relu', kernel_regularizer=l2(0.001)),
    Dropout(0.5),
    
    # Output layer
    Dense(num_classes, activation='softmax')
])

model.compile(
    optimizer=Adam(learning_rate=0.0001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# Data augmentation
print("\n[6/7] Setting up data augmentation...")
datagen = ImageDataGenerator(
    rotation_range=10,
    width_shift_range=0.1,
    height_shift_range=0.1,
    zoom_range=0.1
)
datagen.fit(X_train)

# Train model
print("\n[7/7] Training model (this may take a while)...")
print("Training for 20 epochs with data augmentation...")

history = model.fit(
    datagen.flow(X_train, y_train, batch_size=32),
    epochs=20,
    validation_data=(X_val, y_val),
    verbose=1
)

# Save the trained model
model_path = os.path.join(os.path.dirname(__file__), 'ocr_character_model.h5')
model.save(model_path)
print(f"\n✓ Model saved to: {model_path}")

# Save character mappings
mapping_path = os.path.join(os.path.dirname(__file__), 'char_mappings.npy')
np.save(mapping_path, {'char_to_int': char_to_int, 'int_to_char': int_to_char})
print(f"✓ Character mappings saved to: {mapping_path}")

# Plot training history
print("\nGenerating training plots...")
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.title('Model Accuracy')
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Model Loss')
plt.legend()
plt.grid(True)

plot_path = os.path.join(os.path.dirname(__file__), 'training_history.png')
plt.savefig(plot_path)
print(f"✓ Training plots saved to: {plot_path}")

# Final validation accuracy
final_val_acc = history.history['val_accuracy'][-1] * 100
print(f"\n{'=' * 60}")
print(f"Training Complete!")
print(f"Final Validation Accuracy: {final_val_acc:.2f}%")
print(f"{'=' * 60}")

# Test on testing dataset
print("\n[BONUS] Evaluating on test dataset...")
try:
    test_data = []
    for label in os.listdir(testing_data_path):
        label_path = os.path.join(testing_data_path, label)
        if os.path.isdir(label_path):
            for image_name in os.listdir(label_path)[:10]:  # Sample 10 per class
                img_path = os.path.join(label_path, image_name)
                test_data.append((img_path, label))
    
    test_df = pd.DataFrame(test_data, columns=['image_path', 'label'])
    X_test, y_test = load_images(test_df)
    X_test = X_test.reshape(-1, 32, 32, 1)
    
    y_pred = model.predict(X_test, verbose=0)
    y_pred_labels = np.argmax(y_pred, axis=1)
    predicted_chars = [int_to_char[i] for i in y_pred_labels]
    
    actual_labels = [char_to_int[label] for label in test_df['label']]
    correct = np.sum([1 for p, a in zip(y_pred_labels, actual_labels) if p == a])
    test_accuracy = (correct / len(actual_labels)) * 100
    
    print(f"✓ Test Accuracy on sample: {test_accuracy:.2f}%")
except Exception as e:
    print(f"Could not evaluate on test set: {e}")

print("\n" + "=" * 60)
print("Next Steps:")
print("1. The trained model is saved as 'ocr_character_model.h5'")
print("2. Character mappings are saved as 'char_mappings.npy'")
print("3. Update your ocr.py to use this trained model")
print("=" * 60)
