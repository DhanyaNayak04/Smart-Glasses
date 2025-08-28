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


"""Voice command thread using Vosk, integrated with TTS coordination.

Improved matching uses normalization and a lightweight fuzzy/whole-word
matching strategy to reduce missed commands and handle small transcription
variations (contractions, punctuation, minor typos).
"""
import queue, json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from state import command_queue, tts_lock

import re
import difflib

ALLOWED_COMMANDS = [
    "stop", "start", "exit", "quit",
    "what is in front of me", "what's in front of me",
    "what is infront of me", "what's infront of me"
]


def _normalize_text(s: str) -> str:
    """Lowercase, expand a couple contractions, remove punctuation, and squash spaces."""
    s = s.lower()
    # common contractions handled simply
    s = s.replace("what's", "what is")
    s = s.replace("whats", "what is")
    # remove punctuation
    s = re.sub(r"[^\w\s]", "", s)
    # normalize whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Precompute a normalized mapping from normalized form -> canonical allowed command
_NORMALIZED_TO_COMMAND = { _normalize_text(cmd): cmd for cmd in ALLOWED_COMMANDS }
_NORMALIZED_COMMANDS = list(_NORMALIZED_TO_COMMAND.keys())


def _match_command(recognized_text: str, cutoff: float = 0.65):
    """Try to match recognized_text to one of ALLOWED_COMMANDS.

    Strategy:
    - Normalize the recognized text.
    - Check short single-word commands as whole words (stop/start/exit/quit).
    - Use difflib.get_close_matches against normalized allowed commands.
    - As a final fallback, compare ratio scores and accept best if above cutoff.

    Returns the canonical command (from ALLOWED_COMMANDS) or None.
    """
    norm = _normalize_text(recognized_text)

    # quick whole-word check for short commands
    for short in ("stop", "start", "exit", "quit"):
        if re.search(rf"\b{re.escape(short)}\b", norm):
            return short

    # fuzzy match against normalized phrases
    matches = difflib.get_close_matches(norm, _NORMALIZED_COMMANDS, n=1, cutoff=cutoff)
    if matches:
        return _NORMALIZED_TO_COMMAND[matches[0]]

    # fallback: compute best ratio and accept if above cutoff
    best = None
    best_score = 0.0
    for cand in _NORMALIZED_COMMANDS:
        score = difflib.SequenceMatcher(None, norm, cand).ratio()
        if score > best_score:
            best_score = score
            best = cand
    if best_score >= cutoff:
        return _NORMALIZED_TO_COMMAND[best]
    return None


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
                    matched = _match_command(text)
                    if matched:
                        print(f"[VOSK] Command matched: {matched}")
                        command_queue.put(matched)
