# Obstacle Detection - Visual Explanation

## How It Works Now

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAMERA FRAME                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                           │   │
│  │        [Background / Distant Objects]                    │   │
│  │                                                           │   │
│  │    ┌───────────────────────────────────────┐            │   │
│  │    │                                         │            │   │
│  │    │      CENTRAL REGION (40% x 40%)        │            │   │
│  │    │                                         │            │   │
│  │    │         ┌─────────┐                    │            │   │
│  │    │         │ PERSON  │ ← Detected object │            │   │
│  │    │         │ (18%)   │   (large enough)  │            │   │
│  │    │         └─────────┘                    │            │   │
│  │    │                                         │            │   │
│  │    │         Depth Analysis:                │            │   │
│  │    │         ■■■■■■□□□□ (23% close pixels)  │            │   │
│  │    │                                         │            │   │
│  │    └───────────────────────────────────────┘            │   │
│  │                                                           │   │
│  │        [Small objects ignored]                           │   │
│  │            📕 🍎                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

                          ↓
            ┌─────────────────────────────┐
            │   DETECTION DECISION TREE   │
            └─────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  1. Is object in OBSTACLE_TYPES?   │
        │     ✅ person, car, chair, etc.     │
        │     ❌ book, phone, cup, etc.       │
        └─────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  2. Is object > 15% of frame?       │
        │     ✅ Large object                  │
        │     ❌ Small object (ignored)        │
        └─────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  3. Is object in central region?    │
        │     ✅ Center 40% of frame           │
        │     ❌ Edges/periphery               │
        └─────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  4. Is depth close (< 50% median)?  │
        │     ✅ > 20% of pixels are close     │
        │     ❌ Few close pixels              │
        └─────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │  5. Multi-frame confirmation         │
        │     Frame 1: ✅ Obstacle             │
        │     Frame 2: ✅ Obstacle             │
        │     Frame 3: ❌ No obstacle          │
        │     Result: ✅ (2/3 confirmed)       │
        └─────────────────────────────────────┘
                          ↓
            ┌──────────────────────┐
            │  ⚠️  OBSTACLE ALERT  │
            └──────────────────────┘
```

---

## OLD vs NEW Logic

### OLD (Too Many False Positives) ❌

```
IF (any pixel is close) OR (any object > 5%)
    → TRIGGER WARNING
```

**Problems**:
- Distant small objects triggered
- Walls/floors detected
- Single frame glitches
- No object type filtering

**Example**:
```
Book on table (10% of frame, distant)
  → Depth: some pixels close
  → Object: yes (10% > 5%)
  → OR logic: TRIGGER ❌
```

---

### NEW (Accurate Detection) ✅

```
IF (obstacle-type object) AND
   (object > 15% of frame) AND
   (object in central 40%) AND
   (> 20% pixels are close) AND
   (2 out of 3 frames confirm)
    → TRIGGER WARNING
```

**Improvements**:
- Only relevant objects
- Must be large and central
- Depth confirmation required
- Multi-frame smoothing

**Example**:
```
Book on table (10% of frame, distant)
  → Object type: ❌ (not in OBSTACLE_TYPES)
  → No warning ✅

Person ahead (18% of frame, close)
  → Object type: ✅ (person in list)
  → Size: ✅ (18% > 15%)
  → Position: ✅ (in center)
  → Depth: ✅ (23% pixels close)
  → Frames: ✅ (2/3 confirmed)
  → TRIGGER WARNING ✅
```

---

## Detection Flow Diagram

```
┌──────────────┐
│ Camera Frame │
└──────┬───────┘
       │
       ├─→ YOLO Object Detection
       │   ├─→ Detect all objects
       │   ├─→ Filter by type (OBSTACLE_TYPES)
       │   ├─→ Check size (> 15%)
       │   ├─→ Check position (central 40%)
       │   └─→ [Object Signal: Yes/No]
       │
       └─→ MiDaS Depth Estimation
           ├─→ Analyze central region
           ├─→ Calculate median depth
           ├─→ Count close pixels (< 50% median)
           ├─→ Check ratio (> 20%)
           └─→ [Depth Signal: Yes/No]

                    ↓

       ┌────────────────────────┐
       │  Combine Signals (AND) │
       │  Object ✅ AND Depth ✅ │
       └───────────┬────────────┘
                   │
                   ↓
       ┌────────────────────────┐
       │   Add to History       │
       │   [✅, ✅, ❌]          │
       └───────────┬────────────┘
                   │
                   ↓
       ┌────────────────────────┐
       │  Check Confirmations   │
       │  2 out of 3 = ✅       │
       └───────────┬────────────┘
                   │
                   ├─→ ✅ Confirmed → ⚠️ WARNING
                   └─→ ❌ Not confirmed → Silent
```

---

## Parameters Explained Visually

### Central Region Size (40%)

```
┌───────────────────────────────┐
│ Frame (100% x 100%)           │
│                               │
│   ┌───────────────────┐       │
│   │                   │       │
│   │  Central 40x40%   │       │
│   │  (checked area)   │       │
│   │                   │       │
│   └───────────────────┘       │
│                               │
│  (edges ignored)              │
└───────────────────────────────┘
```

### Depth Threshold (50% of median)

```
Depth Map:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Close    Median      Far
(0)      (50)       (100)
 │         │          │
 ◄────50%─►│          │
   NEAR    │   FAR    │
           │          │
   Triggers│ Ignored  │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Object Size (15% of frame)

```
Frame area = 1000 pixels

Small object (50 px = 5%)
┌─┐
└─┘  → Too small ❌

Medium object (100 px = 10%)
┌───┐
│   │  → Too small ❌
└───┘

Large object (200 px = 20%)
┌──────┐
│      │  → Large enough ✅
│      │
└──────┘
```

### Multi-Frame Smoothing

```
Time →

Frame 1: ✅ Obstacle    ┐
Frame 2: ✅ Obstacle    ├→ 2/3 = Confirmed ✅
Frame 3: ❌ No obstacle ┘

Frame 4: ❌ No obstacle ┐
Frame 5: ❌ No obstacle ├→ 0/3 = Not confirmed ❌
Frame 6: ❌ No obstacle ┘

Frame 7: ✅ Obstacle    ┐
Frame 8: ❌ No obstacle ├→ 1/3 = Not confirmed ❌
Frame 9: ❌ No obstacle ┘
```

---

## Comparison: Same Scene

### Before (False Positive) ❌

```
Scene: Person sitting far away, cup on table nearby

┌───────────────────────────┐
│                           │
│  👤 (far, 8% of frame)   │  → Person: 8% > 5% ✅
│                           │  → Depth: some close ✅
│      ☕ (near, 3%)        │  → Cup: 3% < 5% ❌
│                           │  → Depth: close ✅
└───────────────────────────┘  
                              → OR logic: TRIGGER ❌
                              → "Obstacle detected" (wrong!)
```

### After (Correct) ✅

```
Same scene: Person sitting far away, cup on table nearby

┌───────────────────────────┐
│                           │
│  👤 (far, 8% of frame)   │  → Person: in list ✅
│                           │  → Size: 8% < 15% ❌
│      ☕ (near, 3%)        │  → Cup: not in list ❌
│                           │  
└───────────────────────────┘  
                              → AND logic: No trigger ✅
                              → Silent (correct!)
```

---

## Debug Output Example

```bash
# Normal operation (no obstacle)
[DETECTION] Objects: {'book', 'cup', 'person'} boxes=3
# person is far/small, book/cup not in obstacle types
# No warning ✅

# Obstacle approaching
[DETECTION] Objects: {'person', 'chair'} boxes=2
[DETECTION] Large obstacle detected: person (area=18.50%)
# person is 18.5% of frame, in central region
# Depth check: 23% pixels are close

# Confirmation (2 out of 3 frames)
[DETECTION] ⚠️ Obstacle ahead (depth_ratio=0.23, confirmed=2/3)
# Warning triggered ✅

# Obstacle moves away or user turns
[DETECTION] Obstacle cleared.
# Warning stops ✅
```

---

## Tuning Guide (Visual)

```
        Less Sensitive ←──────────→ More Sensitive
        ════════════════════════════════════════════

Depth:        0.4  ←─── 0.5 ───→  0.6
              Only     Default    Farther
              very                objects
              close               trigger

Near %:       0.25 ←─── 0.20 ──→ 0.15
              More     Default    Fewer
              pixels              pixels
              needed              needed

Size:         0.20 ←─── 0.15 ──→ 0.10
              Only     Default    Smaller
              large               objects
              objects             count

Confirm:      3    ←─── 2 ─────→ 1
              All      Default    Single
              frames              frame
              agree               enough
```

---

This visual guide should help you understand how the obstacle detection works and how to tune it for your needs!
