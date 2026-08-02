import cv2
import time
camera_index_candidates = [1, 0, 2, 3, 4]


def _open_camera():
    for camera_index in camera_index_candidates:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        time.sleep(1)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 0.0
            print(f"camera opened:{width}x{height} @ {fps:.1f} FPS (index {camera_index})")
            return cap, width, height, fps

        cap.release()

    raise RuntimeError("can not open any camera index")


cap, width, height, fps = _open_camera()


def readframe(cap):
    success, frame = cap.read()
    return success, frame


def release_camera(cap):
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("camera released.Application Closed")