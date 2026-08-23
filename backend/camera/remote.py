from __future__ import annotations
import threading
import time
import cv2
import numpy as np
from backend.camera.base import CameraSource


class RemoteCamera(CameraSource):

    def __init__(self, device_id: str, label: str) -> None:
        self._device_id           = device_id
        self._label               = label
        self._lock                = threading.Lock()
        self._latest_frame:        np.ndarray | None = None
        self._latest_jpeg_bytes:   bytes | None = None
        self._width:               int   = 640
        self._height:              int   = 480
        self._is_open:             bool  = True
        self._last_update_time:    float = time.time()
        self._last_capture_ts:     float = 0.0
        self._last_receive_ts:     float = 0.0

    def push_jpeg_bytes(self, jpeg_bytes: bytes, capture_ts: float = 0.0, width: int = 640, height: int = 480) -> None:
        now = time.time()
        with self._lock:
            self._latest_jpeg_bytes = jpeg_bytes
            self._latest_frame      = None
            self._width             = width
            self._height            = height
            self._is_open           = True
            self._last_update_time  = now
            self._last_receive_ts   = now
            if capture_ts > 0:
                self._last_capture_ts = capture_ts

    def push_frame(self, frame: np.ndarray, capture_ts: float = 0.0) -> None:
        now = time.time()
        with self._lock:
            self._latest_frame        = frame
            self._latest_jpeg_bytes  = None
            self._height, self._width = frame.shape[:2]
            self._is_open             = True
            self._last_update_time    = now
            self._last_receive_ts     = now
            if capture_ts > 0:
                self._last_capture_ts = capture_ts

    def get_latest_jpeg(self) -> tuple[bool, bytes | None, float]:
        with self._lock:
            if not self._is_open:
                return False, None, 0.0

            if time.time() - self._last_update_time > 5.0:
                self._is_open = False
                return False, None, 0.0

            if self._latest_jpeg_bytes is not None:
                return True, self._latest_jpeg_bytes, self._last_capture_ts

            if self._latest_frame is not None:
                ok_jpg, buf = cv2.imencode(".jpg", self._latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ok_jpg:
                    self._latest_jpeg_bytes = buf.tobytes()
                    return True, self._latest_jpeg_bytes, self._last_capture_ts

            return False, None, 0.0

    def read(self) -> tuple[bool, object]:
        with self._lock:
            if not self._is_open:
                return False, b""

            if time.time() - self._last_update_time > 5.0:
                self._is_open = False
                return False, b""

            if self._latest_frame is not None:
                return True, self._latest_frame

            if self._latest_jpeg_bytes is not None:
                np_buf = np.frombuffer(self._latest_jpeg_bytes, dtype=np.uint8)
                frame = cv2.imdecode(np_buf, cv2.IMREAD_COLOR)
                if frame is not None:
                    self._latest_frame = frame
                    self._height, self._width = frame.shape[:2]
                    return True, self._latest_frame

            return False, None

    def mark_disconnected(self) -> None:
        with self._lock:
            self._is_open = False
            self._latest_frame = None
            self._latest_jpeg_bytes = None

    def open(self) -> bool:
        with self._lock:
            self._is_open = True
        return True

    def release(self) -> None:
        with self._lock:
            self._is_open = False
            self._latest_frame = None
            self._latest_jpeg_bytes = None
        print(f"[RemoteCamera] Released: {self._label}")

    @property
    def latency_ms(self) -> float:
        with self._lock:
            if self._last_capture_ts > 0 and self._last_receive_ts > 0:
                diff = (self._last_receive_ts - self._last_capture_ts) * 1000.0
                return max(0.0, round(diff, 1))
            return 0.0

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def label(self) -> str:
        with self._lock:
            return self._label

    @label.setter
    def label(self, value: str) -> None:
        with self._lock:
            self._label = value

    @property
    def width(self) -> int:
        with self._lock:
            return self._width

    @property
    def height(self) -> int:
        with self._lock:
            return self._height

    @property
    def fps(self) -> float:
        return 0.0

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._is_open
