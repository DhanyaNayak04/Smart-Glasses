import cv2

def image_capture():
    # Use hardcoded IP camera URL
    ipcam_url = 'http://192.168.0.4:4747/video'
    cap = cv2.VideoCapture(ipcam_url)
    import time
    import os
    print("Capturing an image every 5 seconds. Press ESC in the window to exit.")
    img_count = 0
    last_capture_time = time.time()
    save_dir = "captured_images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    last_filename = None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame. Check the camera URL or connection.")
            break
        cv2.imshow("Camera Feed", frame)

        key = cv2.waitKey(1)
        if key % 256 == 27:
            # Save the current frame when ESC is pressed
            img_count += 1
            filename = os.path.join(save_dir, f"captured_{img_count}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Image saved as {filename}")
            last_filename = filename
            break

        current_time = time.time()
        if current_time - last_capture_time >= 5:
            img_count += 1
            filename = os.path.join(save_dir, f"captured_{img_count}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Image saved as {filename}")
            last_capture_time = current_time
            last_filename = filename

    cap.release()
    cv2.destroyAllWindows()
    return last_filename


if __name__ == "__main__":
    image_capture()
