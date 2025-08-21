import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json

def listen_for_commands():
    """Listen for voice commands and return recognized text."""
    model = Model(lang="en-us")
    recognizer = KaldiRecognizer(model, 16000)
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        print("Listening for commands... (say 'start detection', 'stop detection', 'read this', 'what is this', 'who is this', or 'exit')")
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = json.loads(result)["text"]
                if text:
                    print(f"Recognized: {text}")
                    return text

if __name__ == "__main__":
    while True:
        command = listen_for_commands()
        if "start detection" in command:
            print("Trigger obstacle detection here.")
        elif "stop detection" in command:
            print("Stop obstacle detection here.")
        elif "read this" in command:
            print("Trigger OCR module here.")
        elif "what is this" in command:
            print("Trigger object detection module here.")
        elif "who is this" in command:
            print("Trigger face recognition module here.")
        elif "exit" in command:
            print("Exiting voice command interface.")
            break
        else:
            print("Command not recognized. Try again.")
