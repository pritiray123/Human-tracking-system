from __future__ import annotations
import time
import cv2
import backend.config as config
from backend.camera.base import CameraSource


class LocalCamera(CameraSource):

    def __init__(self) -> None:
        self._cap:                  cv2.VideoCapture | None = None
        self._width:                int   = 0
        self._height:               int   = 0
        self._fps:                  float = 0.0
        self._is_open:              bool  = False
        self._cam_index:            int   = -1
        self._consecutive_failures: int   = 0

    def open(self) -> bool:
        if self._is_open:
            return True

        for idx in config.CAMERA_INDEX_CANDIDATES:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            time.sleep(0.3)

            if not cap.isOpened():
                cap.release()
                continue

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.DEFAULT_FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.DEFAULT_FRAME_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, config.DEFAULT_TARGET_FPS)

            ok, test_frame = cap.read()
            if not ok or test_frame is None:
                cap.release()
                continue

            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or test_frame.shape[1]
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or test_frame.shape[0]

            if w == 0 or h == 0:
                cap.release()
                continue

            fps = cap.get(cv2.CAP_PROP_FPS)
            self._cap                  = cap
            self._width                = w
            self._height               = h
            self._fps                  = fps if fps > 0 else float(config.DEFAULT_TARGET_FPS)
            self._is_open              = True
            self._cam_index            = idx
            self._consecutive_failures = 0
            print(f"[LocalCamera] Opened index {idx}: {w}x{h} @ {self._fps:.1f} FPS")
            return True

        print("[LocalCamera] No working camera found at any candidate index.")
        return False

    def read(self) -> tuple[bool, object]:
        if not self._is_open or self._cap is None:
            return False, b""

        ok, frame = self._cap.read()
        if not ok or frame is None:
            self._consecutive_failures += 1
            if self._consecutive_failures < 10:
                return False, None

            self._is_open = False
            print("[LocalCamera] Frame read failed 10 consecutive times — camera disconnected.")
            return False, b""

        self._consecutive_failures = 0
        return True, frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._is_open = False
        print(f"[LocalCamera] Released (index {self._cam_index}).")

    def mark_disconnected(self) -> None:
        self.release()

    def close(self) -> None:
        self.release()

    @property
    def device_id(self) -> str:
        return "local:0"

    @property
    def label(self) -> str:
        if self._cam_index >= 0:
            return f"Local Camera (index {self._cam_index})"
        return "Local Camera"

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def is_open(self) -> bool:
        return self._is_open
