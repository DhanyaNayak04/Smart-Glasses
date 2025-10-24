# Python Package Repair and Installation Script (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Python Package Repair Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Upgrade pip
Write-Host "[1/6] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --user
Write-Host ""

# Step 2: Fix corrupted requests
Write-Host "[2/6] Fixing corrupted requests package..." -ForegroundColor Yellow
python -m pip install --force-reinstall --no-deps requests --user
Write-Host ""

# Step 3: Install requests dependencies
Write-Host "[3/6] Installing requests dependencies..." -ForegroundColor Yellow
python -m pip install certifi charset-normalizer idna urllib3 --user
Write-Host ""

# Step 4: Install kagglehub
Write-Host "[4/6] Installing kagglehub..." -ForegroundColor Yellow
python -m pip install kagglehub --user
Write-Host ""

# Step 5: Install ML packages
Write-Host "[5/6] Installing TensorFlow and ML packages..." -ForegroundColor Yellow
python -m pip install tensorflow pandas matplotlib scikit-learn --user
Write-Host ""

# Step 6: Install image processing
Write-Host "[6/6] Installing image processing packages..." -ForegroundColor Yellow
python -m pip install Pillow opencv-python numpy --user
Write-Host ""

# Verification
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Testing imports..." -ForegroundColor Yellow
$packages = @(
    @{name="kagglehub"; import="kagglehub"},
    @{name="tensorflow"; import="tensorflow"},
    @{name="pandas"; import="pandas"},
    @{name="opencv"; import="cv2"},
    @{name="pillow"; import="PIL"},
    @{name="numpy"; import="numpy"}
)

foreach ($pkg in $packages) {
    try {
        python -c "import $($pkg.import)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $($pkg.name)" -ForegroundColor Green
        } else {
            Write-Host "✗ $($pkg.name)" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ $($pkg.name)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Next step: python train_ocr_model.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
