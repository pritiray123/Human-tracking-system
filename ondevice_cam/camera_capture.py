import cv2
camera_index=0
cap=cv2.VideoCapture(camera_index)
if not cap.isOpened():
    raise RuntimeError(f"can not open camera at index{camera_index}")

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height=int(cap.get(cv2 .CAP_PROP_FRAME_HEIGHT))
fps= cap.get(cv2.CAP_PROP_FPS)
print(f"camera opened:{width}x{height} @ {fps:.1f} FPS")
