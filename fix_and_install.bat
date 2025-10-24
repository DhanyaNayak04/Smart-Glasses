@echo off
echo ========================================
echo Python Package Repair Script
echo ========================================
echo.

echo [1/6] Upgrading pip...
python -m pip install --upgrade pip --user
echo.

echo [2/6] Fixing corrupted requests package...
python -m pip install --force-reinstall --no-deps requests --user
echo.

echo [3/6] Installing requests dependencies...
python -m pip install certifi charset-normalizer idna urllib3 --user
echo.

echo [4/6] Installing kagglehub...
python -m pip install kagglehub --user
echo.

echo [5/6] Installing TensorFlow and ML packages...
python -m pip install tensorflow pandas matplotlib scikit-learn --user
echo.

echo [6/6] Installing image processing packages...
python -m pip install Pillow opencv-python numpy --user
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Testing imports...
python -c "import kagglehub; print('✓ kagglehub')" 2>nul || echo ✗ kagglehub
python -c "import tensorflow; print('✓ tensorflow')" 2>nul || echo ✗ tensorflow
python -c "import pandas; print('✓ pandas')" 2>nul || echo ✗ pandas
python -c "import cv2; print('✓ opencv')" 2>nul || echo ✗ opencv
echo.

echo Next step: python train_ocr_model.py
echo.
pause
