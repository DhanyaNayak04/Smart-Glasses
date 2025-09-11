# voice_thread.py

import queue
import json
import re
import difflib
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from state import command_queue, tts_lock

ALLOWED_COMMANDS = [
    "stop", "start", "exit", "quit",
    "what is in front of me", "what's in front of me",
    "what is infront of me", "what's infront of me",
    "who is in front of me", "who's in front of me",
    "who is infront of me", "who's infront of me"
]


def _normalize_text(s: str) -> str:
    s = s.lower()
    s = s.replace("what's", "what is")
    s = s.replace("whats", "what is")
    s = s.replace("who's", "who is")
    s = s.replace("whos", "who is")
    s = s.replace("infront", "in front")
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

_NORMALIZED_TO_COMMAND = {_normalize_text(cmd): cmd for cmd in ALLOWED_COMMANDS}
_NORMALIZED_COMMANDS = list(_NORMALIZED_TO_COMMAND.keys())


# --- MODIFIED _match_command FUNCTION ---
def _match_command(recognized_text: str, cutoff: float = 0.7):
    """
    Try to match recognized_text to one of ALLOWED_COMMANDS.
    This version prioritizes an exact match before falling back to fuzzy matching.
    """
    norm = _normalize_text(recognized_text)

    # 1. (NEW) Prioritize an exact match on the normalized text.
    if norm in _NORMALIZED_TO_COMMAND:
        return _NORMALIZED_TO_COMMAND[norm]

    # 2. Check for short, single-word commands.
    for short in ("stop", "start", "exit", "quit"):
        if re.search(rf"\b{re.escape(short)}\b", norm):
            return short

    # 3. (FALLBACK) If no exact match, use fuzzy matching.
    matches = difflib.get_close_matches(norm, _NORMALIZED_COMMANDS, n=1, cutoff=cutoff)
    if matches:
        return _NORMALIZED_TO_COMMAND[matches[0]]

    return None


def voice_command_thread():
    # This function remains unchanged.
    model = Model(lang="en-us")
    recognizer = KaldiRecognizer(model, 16000)
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(f"[VOSK] Status: {status}")
        if not tts_lock.locked():
            q.put(bytes(indata))

    print("[VOSK] Voice command thread started.")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        while True:
            try:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        print(f"[VOSK] Recognized: '{text}'")
                        matched_command = _match_command(text)
                        if matched_command:
                            print(f"[VOSK] Command matched: '{matched_command}'")
                            command_queue.put(matched_command)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[VOSK] Error: {e}")