"""
Quick Start Script - One-Click OCR Model Training
This script handles everything: Kaggle setup check, download, and training.
"""

import os
import sys

def check_kaggle_setup():
    """Check if Kaggle API is properly configured."""
    print("Checking Kaggle API setup...")
    
    kaggle_dir = os.path.expanduser("~/.kaggle")
    kaggle_json = os.path.join(kaggle_dir, "kaggle.json")
    
    # Windows alternative
    if os.name == 'nt':
        kaggle_dir_win = os.path.join(os.path.expanduser("~"), ".kaggle")
        kaggle_json_win = os.path.join(kaggle_dir_win, "kaggle.json")
        if os.path.exists(kaggle_json_win):
            kaggle_json = kaggle_json_win
    
    if not os.path.exists(kaggle_json):
        print("\n" + "=" * 60)
        print("❌ Kaggle API credentials not found!")
        print("=" * 60)
        print("\nTo set up Kaggle API:")
        print("1. Go to: https://www.kaggle.com/settings")
        print("2. Scroll to 'API' section")
        print("3. Click 'Create New API Token'")
        print("4. Download kaggle.json")
        print("5. Move it to:")
        if os.name == 'nt':
            print(f"   {os.path.join(os.path.expanduser('~'), '.kaggle', 'kaggle.json')}")
        else:
            print(f"   ~/.kaggle/kaggle.json")
        print("\n" + "=" * 60)
        return False
    
    print(f"✓ Kaggle credentials found at: {kaggle_json}")
    return True

def install_dependencies():
    """Install required packages."""
    print("\nInstalling dependencies...")
    packages = [
        "kagglehub",
        "tensorflow",
        "pandas",
        "matplotlib",
        "scikit-learn",
        "Pillow",
        "opencv-python"
    ]
    
    for package in packages:
        print(f"  Installing {package}...")
        os.system(f"{sys.executable} -m pip install -q {package}")
    
    print("✓ All dependencies installed")

def main():
    """Main quick start function."""
    print("=" * 60)
    print("OCR MODEL TRAINING - QUICK START")
    print("=" * 60)
    
    # Step 1: Check Kaggle setup
    if not check_kaggle_setup():
        print("\n⚠ Please set up Kaggle API first, then run this script again.")
        input("\nPress Enter to exit...")
        return
    
    # Step 2: Install dependencies
    response = input("\nInstall required packages? (y/n): ").lower()
    if response == 'y':
        install_dependencies()
    
    # Step 3: Run training
    print("\n" + "=" * 60)
    print("Starting model training...")
    print("=" * 60)
    print("\nThis will:")
    print("1. Download ~140MB dataset from Kaggle")
    print("2. Train CNN model (may take 30-60 minutes)")
    print("3. Save trained model for use in your app")
    
    response = input("\nContinue? (y/n): ").lower()
    if response != 'y':
        print("Training cancelled.")
        return
    
    # Import and run training
    print("\nImporting training script...")
    try:
        import train_ocr_model
        print("\n✓ Training completed successfully!")
        print("\nYou can now test the model with:")
        print("  python test_ocr_model.py")
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        print("\nTry running manually:")
        print("  python train_ocr_model.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
    finally:
        input("\nPress Enter to exit...")
