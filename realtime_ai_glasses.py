import threading
import cv2
import time
import queue
import pyttsx3
from ultralytics import YOLO
import torch
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import json
from conversational_ai import gemini_conversation

# Lock for TTS/Vosk coordination
tts_lock = threading.Lock()

# Camera settings
CAMERA_URL = 'http://10.60.170.80:4747/video'  # Updated as per user request
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
engine = pyttsx3.init()
tts_queue = []
tts_queue_lock = threading.Lock()
tts_queue_event = threading.Event()

def tts_worker():
    while True:
        tts_queue_event.wait()
        with tts_queue_lock:
            if not tts_queue:
                tts_queue_event.clear()
                continue
            priority, text = heapq.heappop(tts_queue)
            if text is None:
                break
        with tts_lock:
            engine.say(text)
            engine.runAndWait()

def speak(text, priority=5):
    # Lower priority value = higher priority (alerts=1, conversation=5)
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
    while True:
        with frame_lock:
            frame = latest_frame[0]
        if frame is None:
            time.sleep(0.05)
            continue
        frame_count += 1
        # Run YOLO every 2nd frame for speed
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
            if detected:
                message = "Detected objects: " + ", ".join(detected)
                print(message)
                speak(message, priority=3)
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
            close_zone = depth_map < (depth_map.mean() * 0.6)
            with context_lock:
                obstacle_detected = bool(close_zone.any())
            if close_zone.any():
                print("⚠️ Obstacle detected nearby!")
                speak("Warning! Obstacle detected ahead.", priority=1)
        time.sleep(0.05)

# Voice command thread
def voice_command_thread():
    model = Model(lang="en-us")
    recognizer = KaldiRecognizer(model, 16000)
    q = queue.Queue()
    def callback(indata, frames, time, status):
        if status:
            print(status)
        # Only listen if TTS is not speaking
        if not tts_lock.locked():
            q.put(bytes(indata))
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
                    print(f"Recognized: {text}")
                    command_queue.put(text)

# Main thread: handle commands and conversation
def main():
    threading.Thread(target=tts_worker, daemon=True).start()
    threading.Thread(target=camera_thread, daemon=True).start()
    threading.Thread(target=detection_thread, daemon=True).start()
    threading.Thread(target=voice_command_thread, daemon=True).start()
    speak("Smart glasses system started. Say something or ask a question.")
    while True:
        try:
            command = command_queue.get(timeout=0.1)
        except queue.Empty:
            continue  # No command, keep looping
        if command.strip().lower() in ["exit", "quit"]:
            speak("Goodbye.", priority=5)
            # Stop TTS thread
            with tts_queue_lock:
                heapq.heappush(tts_queue, (10, None))
                tts_queue_event.set()
            break
        elif "what is this" in command or "detect object" in command:
            speak("Object detection is running.", priority=5)
        elif "obstacle" in command or "start detection" in command:
            speak("Obstacle detection is running.", priority=5)
        else:
            # Compose context for Gemini
            with context_lock:
                objects_str = ", ".join(latest_objects) if latest_objects else "none"
                obstacle_str = "yes" if obstacle_detected else "no"
            context_prompt = (
                f"You are an AI assistant for smart glasses. "
                f"The user is seeing: {objects_str}. "
                f"Obstacle detected: {obstacle_str}. "
                f"The user said: {command}. "
                f"Please reply accordingly."
            )
            ai_response = gemini_conversation(context_prompt, api_key=API_KEY, model="gemini-2.0-flash")
            print("Gemini:", ai_response)
            speak(ai_response, priority=5)

if __name__ == "__main__":
    main()
