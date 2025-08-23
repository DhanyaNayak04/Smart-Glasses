# Voice command thread (restored)
def voice_command_thread():
    from vosk import Model, KaldiRecognizer
    import sounddevice as sd
    import json
    model = Model(lang="en-us")
    recognizer = KaldiRecognizer(model, 16000)
    q = queue.Queue()
    # Define allowed commands (partial match allowed)
    allowed_commands = [
        "stop", "start", "exit", "quit",
        "what is in front of me", "what's in front of me",
        "what is infront of me", "what's infront of me"
    ]
    def callback(indata, frames, time, status):
        if status:
            print(status)
        # Only listen if TTS is not speaking
        if not tts_lock.locked():
            q.put(bytes(indata))
    print("[VOSK] Voice command thread started.")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        while True:
            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                continue
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = json.loads(result)["text"]
                if text:
                    print(f"[VOSK] Recognized: {text}")
                    # Allow partial/substring match for commands
                    for cmd in allowed_commands:
                        if cmd in text.lower():
                            print(f"[VOSK] Command matched: {cmd}")
                            command_queue.put(cmd)
                            break
import threading
import cv2
import time
import queue
from gtts import gTTS
from playsound3 import playsound
import tempfile
from ultralytics import YOLO
import torch
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import json
from conversational_ai import gemini_conversation

# Lock for TTS/Vosk coordination
tts_lock = threading.Lock()

# Camera settings
CAMERA_URL = 'http://192.168.0.5:4747/video'  # Updated as per user request
API_KEY = "AIzaSyC1yvPtTKHY3EQ23XCB06lZQEEPdR51euE"

# Load models once
yolo_model = YOLO('yolo11n.pt')
midas = torch.hub.load("intel-isl/MiDaS", "DPT_Hybrid")
midas.eval()
device = torch.device("cpu")
midas.to(device)
midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = midas_transforms.dpt_transform


# Priority TTS queue: (priority, text), lower number = higher priority

import heapq
tts_queue = []
tts_queue_lock = threading.Lock()
tts_queue_event = threading.Event()

def tts_worker():
    print("[TTS] TTS worker started (gTTS mode).")
    while True:
        tts_queue_event.wait()
        with tts_queue_lock:
            if not tts_queue:
                tts_queue_event.clear()
                continue
            priority, text = heapq.heappop(tts_queue)
            if text is None:
                break
        print(f"[TTS] Speaking: {text}")
        with tts_lock:
            try:
                tts = gTTS(text=text, lang='en')
                with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as fp:
                    tts.save(fp.name)
                    playsound(fp.name)
            except Exception as e:
                print(f"[TTS] Error: {e}")

def speak(text, priority=5):
    # Lower priority value = higher priority (alerts=1, conversation=5)
    print(f"[SPEAK] Queued: {text} (priority {priority})")
    with tts_queue_lock:
        heapq.heappush(tts_queue, (priority, text))
        tts_queue_event.set()


# Shared state and context
latest_frame = [None]  # Use a mutable container for thread-safe latest frame
frame_lock = threading.Lock()
command_queue = queue.Queue()
latest_objects = set()
obstacle_detected = False
context_lock = threading.Lock()
# Detection control state
detection_active = [False]  # Mutable for thread-safe control
# Obstacle warning state
obstacle_warning_state = {
    'active': False,  # Is an obstacle currently detected within 1m
    'count': 0       # How many times warning has been spoken for this event
}

# Camera capture thread
def camera_thread():
    while True:
        cap = cv2.VideoCapture(CAMERA_URL)
        if not cap.isOpened():
            speak("Camera could not be opened. Retrying in 3 seconds.")
            time.sleep(3)
            continue
        while True:
            ret, frame = cap.read()
            if not ret:
                speak("Failed to grab frame from camera. Reconnecting...")
                cap.release()
                time.sleep(2)
                break  # Break inner loop to reconnect
            # Always keep only the latest frame
            with frame_lock:
                latest_frame[0] = frame
        cap.release()

# Object and obstacle detection thread
def detection_thread():
    global latest_objects, obstacle_detected
    frame_count = 0
    print("[DETECTION] Detection thread started.")
    while True:
        # Pause detection if not active
        if not detection_active[0]:
            time.sleep(0.1)
            continue
        with frame_lock:
            frame = latest_frame[0]
        if frame is None:
            time.sleep(0.05)
            continue
        frame_count += 1
        # Run YOLO every 2nd frame for speed (object detection results are not announced)
        if frame_count % 2 == 0:
            results = yolo_model(frame)
            names = yolo_model.names
            detected = set()
            frame_count = 0
            while True:
                # Pause detection if not active
                if not detection_active[0]:
                    time.sleep(0.1)
                    continue
                with frame_lock:
                    frame = latest_frame[0]
                if frame is None:
                    time.sleep(0.05)
                    continue
                frame_count += 1
                # Run YOLO every 2nd frame for speed (object detection results are not announced)
                if frame_count % 2 == 0:
                    results = yolo_model(frame)
                    names = yolo_model.names
                    detected = set()
                    for r in results:
                        for box in r.boxes:
                            cls_id = int(box.cls[0])
                            label = names[cls_id]
                            detected.add(label)
                    with context_lock:
                        latest_objects = detected
                    print(f"[DETECTION] Objects detected: {detected}")
                # Run MiDaS every 3rd frame for speed
                if frame_count % 3 == 0:
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
                    # 1 meter threshold: use a fixed value or calibrate as needed
                    # Here, we use a simple threshold: mean * 0.6 is replaced by mean * 0.6 for close, mean * 1.0 for 1m
                    mean_depth = depth_map.mean()
                    one_meter_zone = depth_map < (mean_depth * 1.0)  # Adjust this factor for real calibration
                    with context_lock:
                        obstacle_detected = bool(one_meter_zone.any())
                    # Obstacle warning logic
                    if one_meter_zone.any():
                        if not obstacle_warning_state['active']:
                            obstacle_warning_state['active'] = True
                            obstacle_warning_state['count'] = 0
                        if obstacle_warning_state['count'] < 2:
                            print("[DETECTION] ⚠️ Obstacle detected within 1 meter!")
                            speak("Warning! Obstacle detected ahead.", priority=1)
                            obstacle_warning_state['count'] += 1
                    else:
                        if obstacle_warning_state['active']:
                            print("[DETECTION] Obstacle cleared.")
                        obstacle_warning_state['active'] = False
                        obstacle_warning_state['count'] = 0
                time.sleep(0.05)
            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                continue
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = json.loads(result)["text"]
                if text:
                    print(f"[VOSK] Recognized: {text}")
                    # Allow partial/substring match for commands
                    for cmd in allowed_commands:
                        if cmd in text.lower():
                            print(f"[VOSK] Command matched: {cmd}")
                            command_queue.put(cmd)
                            break

# Main thread: handle commands and conversation
def main():
    threading.Thread(target=tts_worker, daemon=True).start()
    threading.Thread(target=camera_thread, daemon=True).start()
    threading.Thread(target=detection_thread, daemon=True).start()
    threading.Thread(target=voice_command_thread, daemon=True).start()
    speak("Smart glasses system started. Say a command.")
    # TTS test
    speak("TTS test message. If you hear this, TTS is working.", priority=1)
    while True:
        try:
            command = command_queue.get(timeout=0.1)
        except queue.Empty:
            continue  # No command, keep looping
        cmd = command.strip().lower()
        if cmd in ["exit", "quit"]:
            speak("Goodbye.", priority=5)
            # Stop TTS thread
            with tts_queue_lock:
                heapq.heappush(tts_queue, (10, None))
                tts_queue_event.set()
            break
        elif cmd == "stop":
            detection_active[0] = False
            speak("Stopping all detection.", priority=2)
        elif cmd == "start":
            detection_active[0] = True
            speak("Starting detection.", priority=2)
        elif "what is in front of me" in cmd or "what's in front of me" in cmd or "what is infront of me" in cmd or "what's infront of me" in cmd:
            with context_lock:
                objects_str = ", ".join(latest_objects) if latest_objects else "nothing detected"
            speak(f"In front of you: {objects_str}.", priority=2)
        # All other speech is ignored

if __name__ == "__main__":
    main()
