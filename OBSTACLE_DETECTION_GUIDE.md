# Obstacle Detection - Troubleshooting Guide

## Problem: Everything Detected as Obstacle ❌

### What Was Wrong:
1. **Too sensitive depth detection** - 8% threshold was too low
2. **Loose depth threshold** - 70% of median was too generous  
3. **Small object detection** - 5% area caught everything
4. **OR logic** - Either depth OR object would trigger
5. **No smoothing** - Single frame could cause false alarm

### What Was Fixed: ✅

#### 1. **Stricter Depth Detection**
- Central region reduced: 50% → **40%** of frame
- Depth threshold: 70% → **50%** of median depth
- Near pixel ratio: 8% → **20%** of central region

#### 2. **Larger Object Requirement**
- Minimum object size: 5% → **15%** of frame area
- Only specific obstacle types trigger warnings

#### 3. **AND Logic (Not OR)**
- Now requires **BOTH** depth detection **AND** large central object
- Dramatically reduces false positives

#### 4. **Multi-Frame Smoothing**
- Tracks last 3 frames
- Needs **2 out of 3 frames** to confirm obstacle
- Prevents single-frame glitches

---

## How to Adjust Sensitivity

### Option 1: Use Presets (Easiest)

Edit `realtime_ai_glasses.py` and add at the top:

```python
from detection_config import apply_preset

# Choose one:
apply_preset('sensitive')      # Detects more (may have false positives)
apply_preset('balanced')       # Default (recommended)
apply_preset('conservative')   # Detects less (may miss some obstacles)
```

### Option 2: Manual Fine-Tuning

Edit `detection_config.py` and adjust these values:

```python
# Make detection MORE sensitive (catch more obstacles):
DEPTH_THRESHOLD = 0.6          # Was 0.5 - farther objects trigger
NEAR_PIXEL_RATIO = 0.15        # Was 0.20 - fewer pixels needed
MIN_OBJECT_SIZE = 0.10         # Was 0.15 - smaller objects count
MIN_CONFIRMATIONS = 1          # Was 2 - single frame can trigger
REQUIRE_BOTH_SIGNALS = False   # Was True - either signal triggers

# Make detection LESS sensitive (reduce false positives):
DEPTH_THRESHOLD = 0.4          # Was 0.5 - only very close objects
NEAR_PIXEL_RATIO = 0.25        # Was 0.20 - more pixels needed
MIN_OBJECT_SIZE = 0.20         # Was 0.15 - only large objects
MIN_CONFIRMATIONS = 3          # Was 2 - all 3 frames must agree
REQUIRE_BOTH_SIGNALS = True    # Was True - need both signals
```

---

## Obstacle Types

By default, only these objects trigger warnings:

```python
OBSTACLE_TYPES = {
    'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck',
    'chair', 'couch', 'bed', 'dining table', 'bench',
    'potted plant', 'dog', 'cat', 'horse', 'sheep', 'cow'
}
```

### To Add More Objects:
Edit `detection_config.py` and add to `OBSTACLE_TYPES`:

```python
OBSTACLE_TYPES = {
    'person', 'bicycle', 'car',  # existing
    'backpack', 'suitcase',      # add these
    'bottle', 'cup',             # or these
    # ... any YOLO class name
}
```

### To Remove Objects:
Remove items you don't want to trigger warnings:

```python
OBSTACLE_TYPES = {
    'person', 'car', 'truck'  # Only these will trigger
}
```

---

## Testing Your Changes

### 1. Check Current Settings

Run your app and look for the startup message:
```
[DETECTION] Thread started. Config: depth_thresh=0.5, near_ratio=0.20, min_size=0.15
```

### 2. Monitor Detection Messages

Watch the console for:
```
[DETECTION] Objects: {'person', 'chair'} boxes=2
[DETECTION] Large obstacle detected: person (area=18.50%)
[DETECTION] ⚠️ Obstacle ahead (depth_ratio=0.23, confirmed=2/3)
```

### 3. Adjust Based on Behavior

**If too many false positives:**
- Increase `MIN_OBJECT_SIZE` (0.15 → 0.20)
- Increase `NEAR_PIXEL_RATIO` (0.20 → 0.25)
- Increase `MIN_CONFIRMATIONS` (2 → 3)
- Keep `REQUIRE_BOTH_SIGNALS = True`

**If missing real obstacles:**
- Decrease `MIN_OBJECT_SIZE` (0.15 → 0.10)
- Increase `DEPTH_THRESHOLD` (0.5 → 0.6)
- Decrease `MIN_CONFIRMATIONS` (2 → 1)
- Try `REQUIRE_BOTH_SIGNALS = False`

---

## Understanding the Detection Process

### Step 1: Object Detection (YOLO)
- Detects objects in frame
- Filters by obstacle types
- Checks if object is in central region
- Checks if object is large enough (>15% of frame)

### Step 2: Depth Estimation (MiDaS)
- Analyzes central 40% of frame
- Compares pixels to median depth
- Counts how many are "close" (<50% of median)
- Triggers if >20% of pixels are close

### Step 3: Confirmation
- Combines object + depth signals (AND logic)
- Adds result to 3-frame history
- Confirms if 2 out of 3 frames agree
- Triggers warning only when confirmed

### Step 4: Warning
- Speaks "Warning! Obstacle detected ahead"
- Maximum 2 warnings per obstacle
- Clears when obstacle no longer detected

---

## Quick Reference

| Parameter | Default | What It Does | Increase To | Decrease To |
|-----------|---------|--------------|-------------|-------------|
| `DEPTH_THRESHOLD` | 0.5 | Distance threshold | Detect farther | Detect closer only |
| `NEAR_PIXEL_RATIO` | 0.20 | % of pixels close | Need fewer pixels | Need more pixels |
| `MIN_OBJECT_SIZE` | 0.15 | Min object size | Catch smaller objects | Only large objects |
| `MIN_CONFIRMATIONS` | 2 | Frames to confirm | Faster response | Fewer false positives |
| `CENTRAL_REGION_SIZE` | 0.4 | Focus area | Wider coverage | Tighter focus |

---

## Examples

### For Indoor Navigation (More Sensitive)
```python
DEPTH_THRESHOLD = 0.6
NEAR_PIXEL_RATIO = 0.15
MIN_OBJECT_SIZE = 0.10
MIN_CONFIRMATIONS = 2
OBSTACLE_TYPES = {'person', 'chair', 'couch', 'bed', 'dining table', 'bench'}
```

### For Outdoor Walking (Balanced)
```python
DEPTH_THRESHOLD = 0.5
NEAR_PIXEL_RATIO = 0.20
MIN_OBJECT_SIZE = 0.15
MIN_CONFIRMATIONS = 2
OBSTACLE_TYPES = {'person', 'bicycle', 'car', 'motorcycle', 'dog'}
```

### For Crowded Areas (Conservative)
```python
DEPTH_THRESHOLD = 0.4
NEAR_PIXEL_RATIO = 0.25
MIN_OBJECT_SIZE = 0.20
MIN_CONFIRMATIONS = 3
OBSTACLE_TYPES = {'person', 'bicycle', 'car'}
```

---

## Still Having Issues?

### Debug Mode

Add this to see what's happening:

```python
# In detection.py, add after obstacle detection:
print(f"DEBUG: depth_obs={depth_obstacle}, obj_obs={large_central_box}, "
      f"near_ratio={near_ratio:.3f}, history={obstacle_history}")
```

### Common Issues

1. **"Walls detected as obstacles"**
   - Increase `MIN_OBJECT_SIZE` (walls have no bounding box)
   - This is why we use AND logic (need both depth + object)

2. **"Small items trigger warnings"**
   - Increase `MIN_OBJECT_SIZE` to 0.20 or higher
   - Remove small items from `OBSTACLE_TYPES`

3. **"Missing obstacles in periphery"**
   - Increase `CENTRAL_REGION_SIZE` to 0.5 or 0.6
   - Note: May increase false positives

4. **"Flickering warnings"**
   - Increase `MIN_CONFIRMATIONS` to 3
   - Increase `HISTORY_SIZE` to 4 or 5

---

**Need more help?** Check the console output for detection messages and adjust parameters based on the feedback!
