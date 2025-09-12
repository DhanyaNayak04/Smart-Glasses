"""Orchestration entrypoint for the modular smart glasses system."""
import threading, queue, heapq
from tts import tts_worker, speak
from camera import camera_thread
from detection import detection_thread
from voice_thread import voice_command_thread
from ocr import read_text_from_frame

from state import command_queue, detection_active, latest_objects, context_lock, tts_queue, tts_queue_lock, tts_queue_event, latest_frame, frame_lock, latest_boxes
from facenet_recognition import recognize_face


def main():
    threading.Thread(target=tts_worker, daemon=True).start()
    threading.Thread(target=camera_thread, daemon=True).start()
    threading.Thread(target=detection_thread, daemon=True).start()
    threading.Thread(target=voice_command_thread, daemon=True).start()
    speak("Smart glasses system started. Say a command.")
    speak("TTS test message. If you hear this, TTS is working.", priority=1)
    while True:
        try:
            command = command_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        cmd = command.strip().lower()
        if cmd in ["exit", "quit"]:
            speak("Goodbye.", priority=5)
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
        elif any(phrase in cmd for phrase in ["what is in front of me", "what's in front of me", "what is infront of me", "what's infront of me"]):
            with context_lock:
                objects_str = ", ".join(latest_objects) if latest_objects else "nothing detected"
            speak(f"In front of you: {objects_str}.", priority=2)
        elif any(phrase in cmd for phrase in ["who is in front of me", "who's in front of me", "who is infront of me", "who's infront of me"]):
            # Get the latest frame and run face recognition
            with frame_lock:
                frame = latest_frame[0]
            if frame is not None:
                recognize_face(frame)
            else:
                speak("No camera frame available for face recognition.")
        elif any(phrase in cmd for phrase in ["read this", "read that", "read the text", "read text", "read"]):
            # Perform OCR on latest frame and speak the detected text.
            with frame_lock:
                frame = latest_frame[0]
                boxes = list(latest_boxes)  # copy to avoid locking while OCR runs
            if frame is None:
                speak("No camera frame available to read from.")
                continue
            text = read_text_from_frame(frame, boxes=boxes)
            if not text:
                speak("I couldn't detect any readable text.")
            else:
                # If text is long, trim and speak a summary first
                text = text.strip()
                if len(text) > 300:
                    # speak first sentence or first 250 chars
                    first_sentence = text.split('\n')[0][:250]
                    speak(f"I detected a long text. Starting: {first_sentence} ")
                    speak("Reading the rest now.")
                    speak(text)
                else:
                    speak(text)


if __name__ == "__main__":
    main()
