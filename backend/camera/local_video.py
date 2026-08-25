from __future__ import annotations
import os
import threading
import time
import cv2
import numpy as np
import backend.config as config
from backend.camera.base import CameraSource


class LocalVideoSource(CameraSource):

    def __init__(self, filepath: str, filename: str, device_id: str = "local:0") -> None:
        self._filepath: str       = filepath
        self._filename: str       = filename
        self._device_id: str      = device_id
        self._cap: cv2.VideoCapture | None = None
        self._width: int          = 640
        self._height: int         = 480
        self._fps: float          = 30.0
        self._total_frames: int   = 0
        self._is_open: bool       = False
        self._playback_state: str = "STOPPED"
        self._loop: bool          = True
        self._lock                = threading.Lock()
        self._current_frame: np.ndarray | None = None
        self._last_read_time: float = 0.0

    def open(self) -> bool:
        with self._lock:
            if self._is_open and self._cap is not None:
                return True

            if not os.path.exists(self._filepath):
                print(f"[LocalVideoSource] ERROR: File not found: {self._filepath}")
                return False

            cap = cv2.VideoCapture(self._filepath)
            if not cap.isOpened():
                print(f"[LocalVideoSource] ERROR: Failed to open video: {self._filepath}")
                cap.release()
                return False

            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            ok, frame = cap.read()
            if not ok or frame is None:
                print(f"[LocalVideoSource] ERROR: Cannot read initial frame: {self._filepath}")
                cap.release()
                return False

            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._cap = cap
            self._width = w if w > 0 else frame.shape[1]
            self._height = h if h > 0 else frame.shape[0]
            self._fps = fps if (fps and fps > 0) else float(config.DEFAULT_TARGET_FPS)
            self._total_frames = total
            self._current_frame = frame
            self._is_open = True
            self._playback_state = "PLAYING"
            self._last_read_time = time.time()
            print(f"[LocalVideoSource] Opened '{self._filename}': {self._width}x{self._height} @ {self._fps:.1f} FPS ({self._total_frames} frames)")
            return True

    def read(self) -> tuple[bool, object]:
        with self._lock:
            if not self._is_open or self._cap is None:
                return False, b""

            if self._playback_state in ("PAUSED", "STOPPED"):
                if self._current_frame is not None:
                    return True, self._current_frame
                return False, None

            now = time.time()
            frame_interval = 1.0 / self._fps if self._fps > 0 else 0.033
            elapsed = now - self._last_read_time

            if elapsed < frame_interval and self._current_frame is not None:
                return True, self._current_frame

            ok, frame = self._cap.read()
            if not ok or frame is None:
                if self._loop:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = self._cap.read()

                if not ok or frame is None:
                    self._playback_state = "STOPPED"
                    if self._current_frame is not None:
                        return True, self._current_frame
                    return False, None

            self._current_frame = frame
            self._last_read_time = now
            return True, frame

    def play(self) -> bool:
        with self._lock:
            if not self._is_open:
                return False
            self._playback_state = "PLAYING"
            print(f"[LocalVideoSource] Play '{self._filename}'")
            return True

    def pause(self) -> bool:
        with self._lock:
            if not self._is_open:
                return False
            self._playback_state = "PAUSED"
            print(f"[LocalVideoSource] Pause '{self._filename}'")
            return True

    def stop(self) -> bool:
        with self._lock:
            if not self._is_open:
                return False
            self._playback_state = "STOPPED"
            if self._cap is not None:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            print(f"[LocalVideoSource] Stop '{self._filename}'")
            return True

    def restart(self) -> bool:
        with self._lock:
            if not self._is_open:
                return False
            if self._cap is not None:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._playback_state = "PLAYING"
            print(f"[LocalVideoSource] Restart '{self._filename}'")
            return True

    def set_loop(self, loop: bool) -> None:
        with self._lock:
            self._loop = loop
            print(f"[LocalVideoSource] Loop set to {loop} for '{self._filename}'")

    def release(self) -> None:
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
            self._is_open = False
            self._playback_state = "STOPPED"
            self._current_frame = None
            print(f"[LocalVideoSource] Released '{self._filename}'")

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def label(self) -> str:
        return f"Laptop Video — {self._filename}"

    @property
    def source_type(self) -> str:
        return "video"

    @property
    def source_name(self) -> str:
        return self._filename

    @property
    def playback_state(self) -> str:
        with self._lock:
            if not self._is_open:
                return "STOPPED"
            return self._playback_state

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
        with self._lock:
            return self._is_open
