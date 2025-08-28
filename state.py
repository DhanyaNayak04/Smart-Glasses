"""Shared mutable state and synchronization primitives."""
import threading, queue

# Locks and events
tts_lock = threading.Lock()

# Queues / priority queue infra
import heapq

tts_queue = []  # list of (priority, text)
tts_queue_lock = threading.Lock()
tts_queue_event = threading.Event()

# Command queue from voice recognition
command_queue = queue.Queue()

# Frame / detection state
latest_frame = [None]  # mutable container for latest frame
frame_lock = threading.Lock()

latest_objects = set()
obstacle_detected = False
context_lock = threading.Lock()

# Detection active flag (mutable container so threads see updates)
detection_active = [False]

# Obstacle warning bookkeeping
obstacle_warning_state = {
    'active': False,
    'count': 0,
}
