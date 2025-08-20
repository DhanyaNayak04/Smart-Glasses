import cv2
import pyttsx3

from ultralytics import YOLO
import cv2
import pyttsx3
from image_capture import image_capture
def detect_objects():
    # Capture image using image_capture function
    image_path = image_capture()  # Should return the filename of the captured image
    model = YOLO('yolo11n.pt')  # Use 'yolov8n' for speed
    results = model(image_path)
    names = model.names

    engine = pyttsx3.init()

    detected = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = names[cls_id]
            detected.append(label)

    if detected:
        message = "Detected objects: " + ", ".join(set(detected))
        print(message)
        engine.say(message)
        engine.runAndWait()

if __name__ == "__main__":
    detect_objects()
