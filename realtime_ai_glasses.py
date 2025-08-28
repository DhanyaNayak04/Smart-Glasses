"""Orchestration entrypoint for the modular smart glasses system."""
import threading, queue, heapq
from tts import tts_worker, speak
from camera import camera_thread
from detection import detection_thread
from voice_thread import voice_command_thread
from state import command_queue, detection_active, latest_objects, context_lock, tts_queue, tts_queue_lock, tts_queue_event


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


if __name__ == "__main__":
    main()
