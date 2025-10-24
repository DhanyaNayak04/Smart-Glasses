"""Object and obstacle detection thread.

Adjustments:
- Refined obstacle detection to reduce false positives:
  * Tighter central region focus (40% vs 50% of frame)
  * More conservative depth threshold (50% vs 70% of median)
  * Higher near-pixel ratio requirement (20% vs 8%)
  * Larger object size requirement (15% vs 5% of frame)
  * Only specific obstacle-type objects trigger warnings
  * Requires BOTH depth AND object detection (AND vs OR logic)
  * Multi-frame smoothing (2 out of 3 frames must agree)
"""
import time, cv2, torch, numpy as np
from models import yolo_model, midas, transform, device
from state import (
    latest_frame, frame_lock, latest_objects, latest_boxes, context_lock, obstacle_detected,
    obstacle_warning_state, detection_active
)
from tts import speak
from detection_config import (
    CENTRAL_REGION_SIZE, DEPTH_THRESHOLD, NEAR_PIXEL_RATIO, MIN_OBJECT_SIZE,
    OBSTACLE_TYPES, HISTORY_SIZE, MIN_CONFIRMATIONS, REQUIRE_BOTH_SIGNALS,
    MAX_WARNING_COUNT, DETECTION_FRAME_SKIP
)


def detection_thread():
    global latest_objects, obstacle_detected
    frame_count = 0
    # Obstacle detection smoothing: require multiple consecutive frames
    obstacle_history = []  # Store last N detections
    print(f"[DETECTION] Thread started. Config: depth_thresh={DEPTH_THRESHOLD}, near_ratio={NEAR_PIXEL_RATIO}, min_size={MIN_OBJECT_SIZE}")
    while True:
        if not detection_active[0]:
            time.sleep(0.1)
            continue
        with frame_lock:
            frame = latest_frame[0]
        if frame is None:
            time.sleep(0.05)
            continue
        frame_count += 1
        if frame_count % 2 == 0:
            results = yolo_model(frame)
            names = yolo_model.names
            detected = set()
            boxes_list = []
            h_frame, w_frame = frame.shape[:2]
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = names[cls_id]
                    detected.add(label)
                    # box.xyxy format: tensor of shape (4,)
                    xyxy = box.xyxy[0].cpu().numpy() if hasattr(box, 'xyxy') else None
                    if xyxy is not None:
                        x1, y1, x2, y2 = xyxy
                        area = max(0.0, (x2 - x1) * (y2 - y1))
                        boxes_list.append({
                            'label': label,
                            'xyxy': (float(x1), float(y1), float(x2), float(y2)),
                            'area': float(area),
                            'rel_area': float(area) / (w_frame * h_frame)
                        })
            with context_lock:
                # IMPORTANT: mutate the shared set/list in-place so other modules
                # holding a reference (imported from state) see updates.
                latest_objects.clear()
                latest_objects.update(detected)
                latest_boxes.clear()
                latest_boxes.extend(boxes_list)
            print(f"[DETECTION] Objects: {detected} boxes={len(boxes_list)}")
        if frame_count % DETECTION_FRAME_SKIP == 0:
            # Depth estimation
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            input_batch = transform(img_rgb).to(device)
            with torch.no_grad():
                prediction = midas(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=frame.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            depth_map = prediction.cpu().numpy()

            # Focus on central region (reduces edges / background influence)
            h, w = depth_map.shape
            ch, cw = int(h * CENTRAL_REGION_SIZE), int(w * CENTRAL_REGION_SIZE)
            y0, x0 = (h - ch) // 2, (w - cw) // 2
            roi = depth_map[y0:y0 + ch, x0:x0 + cw]

            # Median-based relative threshold (MiDaS depth is relative, not metric)
            median_depth = np.median(roi)
            if median_depth <= 0:
                near_ratio = 0.0
            else:
                # Objects closer than (median * DEPTH_THRESHOLD)
                near_mask = roi < (median_depth * DEPTH_THRESHOLD)
                near_ratio = near_mask.mean()

            # Check if enough pixels are close
            depth_obstacle = near_ratio > NEAR_PIXEL_RATIO

            # Also consider large bounding boxes in central region as obstacle
            # But only for specific obstacle-type objects
            large_central_box = False
            try:
                cx_min, cy_min = x0, y0
                cx_max, cy_max = x0 + cw, y0 + ch
                for b in latest_boxes:
                    x1, y1, x2, y2 = b['xyxy']
                    # box centroid
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    # Check if object is in obstacle types and large enough
                    is_obstacle_type = b.get('label', '') in OBSTACLE_TYPES
                    if is_obstacle_type and b.get('rel_area', 0.0) >= MIN_OBJECT_SIZE and (cx_min <= cx <= cx_max) and (cy_min <= cy <= cy_max):
                        large_central_box = True
                        print(f"[DETECTION] Large obstacle detected: {b.get('label')} (area={b.get('rel_area', 0.0):.2%})")
                        break
            except Exception as e:
                print(f"[DETECTION] Error checking boxes: {e}")
                large_central_box = False

            # Combine signals based on configuration
            if REQUIRE_BOTH_SIGNALS:
                obstacle_now = depth_obstacle and large_central_box
            else:
                obstacle_now = depth_obstacle or large_central_box
            
            # Smoothing: add to history and check consensus
            obstacle_history.append(obstacle_now)
            if len(obstacle_history) > HISTORY_SIZE:
                obstacle_history.pop(0)
            
            # Require minimum confirmations from recent frames
            obstacle_confirmed = sum(obstacle_history) >= MIN_CONFIRMATIONS

            with context_lock:
                obstacle_detected[0] = bool(obstacle_confirmed)

            if obstacle_confirmed:
                if not obstacle_warning_state['active']:
                    obstacle_warning_state['active'] = True
                    obstacle_warning_state['count'] = 0
                if obstacle_warning_state['count'] < MAX_WARNING_COUNT:
                    print(f"[DETECTION] ⚠️ Obstacle ahead (depth_ratio={near_ratio:.2f}, confirmed={sum(obstacle_history)}/{len(obstacle_history)})")
                    speak("Warning! Obstacle detected ahead.", priority=1)
                    obstacle_warning_state['count'] += 1
            else:
                if obstacle_warning_state['active']:
                    print("[DETECTION] Obstacle cleared.")
                obstacle_warning_state['active'] = False
                obstacle_warning_state['count'] = 0
        time.sleep(0.05)
