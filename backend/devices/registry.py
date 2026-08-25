from __future__ import annotations
import threading
from typing import Optional
from backend.camera.base import CameraSource


class DeviceRegistry:

    def __init__(self) -> None:
        self._lock       = threading.Lock()
        self._devices:   dict[str, CameraSource] = {}
        self._active_id: Optional[str] = None

    def add(self, cam: CameraSource) -> None:
        with self._lock:
            old_cam = self._devices.get(cam.device_id)
            if old_cam is not None and old_cam is not cam:
                try:
                    old_cam.release()
                except Exception as e:
                    print(f"[HTS Registry] Exception releasing replaced device '{cam.device_id}': {e}")
            self._devices[cam.device_id] = cam
            if self._active_id is None or self._active_id not in self._devices:
                self._active_id = cam.device_id
                print(f"[HTS Backend] Auto-set active device to: '{self._active_id}'")


    def remove(self, device_id: str) -> None:
        with self._lock:
            cam = self._devices.pop(device_id, None)
            if cam is not None:
                try:
                    cam.release()
                except Exception:
                    pass
            if self._active_id == device_id:
                self._active_id = next(iter(self._devices), None)
                print(f"[HTS Backend] Device removed. Active device fallback to: '{self._active_id}'")

    def set_active(self, device_id: str) -> bool:
        with self._lock:
            if device_id not in self._devices:
                print(f"[HTS Backend] ERROR: Attempted to activate unknown device: '{device_id}'")
                return False
            self._active_id = device_id
            print(f"[HTS Backend] Active device set to: '{device_id}'")
            return True

    def release_all(self) -> None:
        with self._lock:
            for cam in self._devices.values():
                try:
                    cam.release()
                except Exception:
                    pass
            self._devices.clear()
            self._active_id = None

    def get_active(self) -> Optional[CameraSource]:
        with self._lock:
            if self._active_id is None or self._active_id not in self._devices:
                self._active_id = next(iter(self._devices), None)
            if self._active_id is None:
                return None
            cam = self._devices.get(self._active_id)
            if cam is not None and not cam.is_open:
                for alt_id, alt_cam in self._devices.items():
                    if alt_cam.is_open:
                        self._active_id = alt_id
                        print(f"[HTS Backend] Active camera unresponsive. Auto-switched to: '{alt_id}'")
                        return alt_cam
            return cam

    def get(self, device_id: str) -> Optional[CameraSource]:
        with self._lock:
            return self._devices.get(device_id)

    def list_devices(self) -> list[tuple[str, CameraSource, bool]]:
        with self._lock:
            if self._active_id is None or self._active_id not in self._devices:
                self._active_id = next(iter(self._devices), None)
            return [
                (did, cam, did == self._active_id)
                for did, cam in self._devices.items()
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._devices)


registry = DeviceRegistry()
