import cv2
import time

from phase1_camera.camera_capture import cap, height, readframe, release_camera, width

WINDOW_NAME = "HTS"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, width, height)

is_running = True
prev_time = time.time()


def window_closed(window_name):
    try:
        return cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True

try:
    while is_running:
        success, frame = readframe(cap)

        if not success:
            print("Frame read failed. Camera may have disconnected")
            is_running = False
            continue

        curr_time = time.time()
        loop_fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        cv2.putText(
            frame,
            f"fps:{loop_fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
        )
        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF

        if window_closed(WINDOW_NAME):
            is_running = False
            continue

        if key == ord("q"):
            is_running = False
finally:
    release_camera(cap)