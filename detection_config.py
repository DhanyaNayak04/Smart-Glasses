"""
Obstacle Detection Configuration
Adjust these parameters to fine-tune obstacle detection sensitivity.
"""

# ===== DEPTH-BASED DETECTION =====

# Central region size (fraction of frame)
# Lower = tighter focus, higher = wider coverage
# Default: 0.4 (40% of frame width/height)
CENTRAL_REGION_SIZE = 0.4

# Depth threshold (fraction of median depth)
# Lower = more sensitive, higher = less sensitive
# Objects closer than (median * this value) are considered "near"
# Default: 0.5 (50% of median depth)
DEPTH_THRESHOLD = 0.5

# Near pixel ratio threshold
# Fraction of central region pixels that must be "near" to trigger
# Lower = more sensitive, higher = less sensitive
# Default: 0.20 (20% of central region)
NEAR_PIXEL_RATIO = 0.20


# ===== OBJECT-BASED DETECTION =====

# Minimum object size (fraction of total frame area)
# Objects smaller than this are ignored
# Default: 0.15 (15% of frame)
MIN_OBJECT_SIZE = 0.15

# Obstacle types (only these objects trigger warnings)
# Add/remove object types based on your YOLO model classes
OBSTACLE_TYPES = {
    'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck',
    'chair', 'couch', 'bed', 'dining table', 'bench',
    'potted plant', 'dog', 'cat', 'horse', 'sheep', 'cow'
}


# ===== SMOOTHING & CONFIRMATION =====

# Number of frames to track for smoothing
# Higher = slower response but fewer false positives
# Default: 3 frames
HISTORY_SIZE = 3

# Minimum confirmations needed
# How many frames out of HISTORY_SIZE must detect obstacle
# Default: 2 (need 2 out of 3 frames)
MIN_CONFIRMATIONS = 2

# Require both depth AND object detection
# True = stricter (both must detect), False = either can trigger
# Default: True (AND logic reduces false positives)
REQUIRE_BOTH_SIGNALS = True


# ===== WARNING BEHAVIOR =====

# Maximum number of repeated warnings
# Prevents spam when obstacle is persistent
# Default: 2 warnings
MAX_WARNING_COUNT = 2

# Detection frame skip (process every Nth frame)
# Higher = faster but less frequent updates
# Default: 3 (process every 3rd frame)
DETECTION_FRAME_SKIP = 3


# ===== PRESETS =====

def apply_preset(preset_name):
    """Apply a preset configuration.
    
    Presets:
        'sensitive' - Detect more obstacles (may have false positives)
        'balanced' - Default balanced settings
        'conservative' - Detect fewer obstacles (may miss some)
    """
    global DEPTH_THRESHOLD, NEAR_PIXEL_RATIO, MIN_OBJECT_SIZE
    global MIN_CONFIRMATIONS, REQUIRE_BOTH_SIGNALS
    
    if preset_name == 'sensitive':
        DEPTH_THRESHOLD = 0.6
        NEAR_PIXEL_RATIO = 0.15
        MIN_OBJECT_SIZE = 0.10
        MIN_CONFIRMATIONS = 1
        REQUIRE_BOTH_SIGNALS = False
        print("[CONFIG] Applied 'sensitive' preset")
        
    elif preset_name == 'balanced':
        DEPTH_THRESHOLD = 0.5
        NEAR_PIXEL_RATIO = 0.20
        MIN_OBJECT_SIZE = 0.15
        MIN_CONFIRMATIONS = 2
        REQUIRE_BOTH_SIGNALS = True
        print("[CONFIG] Applied 'balanced' preset (default)")
        
    elif preset_name == 'conservative':
        DEPTH_THRESHOLD = 0.4
        NEAR_PIXEL_RATIO = 0.25
        MIN_OBJECT_SIZE = 0.20
        MIN_CONFIRMATIONS = 3
        REQUIRE_BOTH_SIGNALS = True
        print("[CONFIG] Applied 'conservative' preset")
        
    else:
        print(f"[CONFIG] Unknown preset '{preset_name}', keeping current settings")


# Usage examples:
# From detection.py, import and use:
#   from detection_config import DEPTH_THRESHOLD, NEAR_PIXEL_RATIO, ...
# 
# To change sensitivity at runtime:
#   from detection_config import apply_preset
#   apply_preset('sensitive')  # or 'balanced' or 'conservative'
