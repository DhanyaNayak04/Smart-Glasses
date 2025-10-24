"""
Fix corrupted pip packages and install dependencies.
This script repairs corrupted package metadata and installs required packages.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and print status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors/Warnings:", result.stderr)
    
    return result.returncode == 0

def main():
    print("Python Package Repair and Installation Script")
    print("="*60)
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    
    # Step 1: Upgrade pip itself
    print("\n[Step 1/5] Upgrading pip...")
    run_command(
        f'"{sys.executable}" -m pip install --upgrade pip --user',
        "Upgrading pip to latest version"
    )
    
    # Step 2: Fix corrupted requests package
    print("\n[Step 2/5] Fixing corrupted requests package...")
    run_command(
        f'"{sys.executable}" -m pip install --force-reinstall --no-deps requests --user',
        "Force reinstalling requests package"
    )
    
    # Step 3: Reinstall dependencies for requests
    print("\n[Step 3/5] Installing requests dependencies...")
    run_command(
        f'"{sys.executable}" -m pip install certifi charset-normalizer idna urllib3 --user',
        "Installing requests dependencies"
    )
    
    # Step 4: Install kagglehub
    print("\n[Step 4/5] Installing kagglehub...")
    success = run_command(
        f'"{sys.executable}" -m pip install kagglehub --user',
        "Installing kagglehub"
    )
    
    if not success:
        print("\n⚠ Trying alternative installation method...")
        run_command(
            f'"{sys.executable}" -m pip install --no-cache-dir kagglehub --user',
            "Installing kagglehub (no cache)"
        )
    
    # Step 5: Install all other required packages
    print("\n[Step 5/5] Installing other required packages...")
    
    packages = [
        'tensorflow',
        'pandas',
        'matplotlib',
        'scikit-learn',
        'Pillow',
        'opencv-python',
        'numpy'
    ]
    
    for package in packages:
        print(f"\nInstalling {package}...")
        run_command(
            f'"{sys.executable}" -m pip install {package} --user',
            f"Installing {package}"
        )
    
    # Verify installations
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    test_imports = [
        ('kagglehub', 'Kaggle Hub'),
        ('tensorflow', 'TensorFlow'),
        ('pandas', 'Pandas'),
        ('matplotlib', 'Matplotlib'),
        ('sklearn', 'Scikit-learn'),
        ('PIL', 'Pillow'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy')
    ]
    
    print("\nTesting imports...")
    failed = []
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - FAILED")
            failed.append(name)
    
    print("\n" + "="*60)
    if failed:
        print(f"⚠ {len(failed)} package(s) failed to import: {', '.join(failed)}")
        print("\nYou may need to:")
        print("1. Close and reopen your terminal/IDE")
        print("2. Run this script again")
        print("3. Or install manually: pip install <package> --user")
    else:
        print("✓ All packages installed successfully!")
        print("\nYou can now run:")
        print("  python train_ocr_model.py")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")
