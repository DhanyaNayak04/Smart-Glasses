"""Voice command thread using Vosk, integrated with TTS coordination."""
import queue, json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from state import command_queue, tts_lock

ALLOWED_COMMANDS = [
    "stop", "start", "exit", "quit",
    "what is in front of me", "what's in front of me",
    "what is infront of me", "what's infront of me"
]


def voice_command_thread():
    model = Model(lang="en-us")
    recognizer = KaldiRecognizer(model, 16000)
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status)
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
                    for cmd in ALLOWED_COMMANDS:
                        if cmd in text.lower():
                            print(f"[VOSK] Command matched: {cmd}")
                            command_queue.put(cmd)
                            break
