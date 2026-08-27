from __future__ import annotations
import threading
import time
from types import SimpleNamespace
import cv2
import numpy as np


class DeviceTrackingState:
    def __init__(self, device_id: str) -> None:
        self.device_id: str = device_id
        self.enabled: bool = False
        self.tracker: object | None = None
        self.frame_counter: int = 0
        self.last_processed_frame_id: int = -1
        self.cached_boxes: list[dict] = []  # list of {"bbox": (x1, y1, x2, y2), "track_id": int, "conf": float}
        self.cached_processed_frame: np.ndarray | None = None
        self.inference_ms: float = 0.0
        self.fps: float = 0.0
        self.last_frame_time: float = time.time()
        self.unprocessed_slot: tuple[np.ndarray, int] | None = None
        self.is_worker_running: bool = False
        self.lock = threading.Lock()

    def reset_tracker_state(self) -> None:
        with self.lock:
            self.tracker = None
            self.frame_counter = 0
            self.last_processed_frame_id = -1
            self.cached_boxes = []
            self.cached_processed_frame = None
            self.inference_ms = 0.0
            self.unprocessed_slot = None


class HumanTracker:
    _instance: HumanTracker | None = None
    _init_lock = threading.Lock()

    def __new__(cls) -> HumanTracker:
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._model = None
        self._model_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._device_states: dict[str, DeviceTrackingState] = {}
        self.detection_interval: int = 2  # Run detection on every 2nd frame
        self.max_inference_size: int = 640
        self._load_model()

    def _load_model(self) -> None:
        try:
            from ultralytics import YOLO
            print("[TRACKER] Loading YOLO model: yolov8n.pt...")
            self._model = YOLO("yolov8n.pt")
            print("[TRACKER] YOLO model loaded successfully")
        except Exception as e:
            print(f"[TRACKER] Failed to load YOLO model: {e}")
            self._model = None

    def _get_device_state(self, device_id: str) -> DeviceTrackingState:
        with self._state_lock:
            if device_id not in self._device_states:
                self._device_states[device_id] = DeviceTrackingState(device_id)
            return self._device_states[device_id]

    def is_enabled(self, device_id: str) -> bool:
        state = self._get_device_state(device_id)
        return state.enabled

    def set_enabled(self, device_id: str, enabled: bool) -> bool:
        state = self._get_device_state(device_id)
        with self._state_lock:
            state.enabled = enabled
            if not enabled:
                state.reset_tracker_state()
        print(f"[TRACKER] tracking enabled for {device_id}: {enabled}")
        return enabled

    def reset_tracker(self, device_id: str) -> None:
        with self._state_lock:
            if device_id in self._device_states:
                print(f"[TRACKER] Resetting tracker state for device={device_id}")
                self._device_states[device_id].reset_tracker_state()

    def _create_tracker(self) -> object | None:
        try:
            try:
                from ultralytics.trackers.byte_tracker import BYTETracker
            except ImportError:
                from ultralytics.trackers import BYTETracker

            args = SimpleNamespace(
                track_high_thresh=0.5,
                track_low_thresh=0.1,
                new_track_thresh=0.6,
                track_buffer=30,
                match_thresh=0.8,
                fuse_score=True
            )
            try:
                return BYTETracker(args)
            except Exception:
                return BYTETracker(args, frame_rate=30)
        except Exception as e:
            print(f"[TRACKER] BYTETracker direct init warning: {e}")
            return None

    def submit_frame(self, device_id: str, frame: np.ndarray, frame_id: int) -> None:
        """Stores the latest frame for background AI processing (Latest-Frame-Wins, non-blocking)."""
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return

        state = self._get_device_state(device_id)
        if not state.enabled or self._model is None:
            return

        with state.lock:
            # Overwrite slot with latest frame (Latest-Frame-Wins)
            state.unprocessed_slot = (frame, frame_id)
            if not state.is_worker_running:
                state.is_worker_running = True
                threading.Thread(target=self._ai_worker_loop, args=(state,), daemon=True).start()

    def _ai_worker_loop(self, state: DeviceTrackingState) -> None:
        """Background AI processing loop running inference on latest frame slot."""
        while True:
            item = None
            with state.lock:
                if not state.enabled or state.unprocessed_slot is None or self._model is None:
                    state.is_worker_running = False
                    return
                item = state.unprocessed_slot
                state.unprocessed_slot = None  # Consume slot

            frame, frame_id = item
            state.frame_counter += 1

            # Run detection on alternate frames or if no cached boxes exist
            if (state.frame_counter % self.detection_interval == 0) or len(state.cached_boxes) == 0:
                self._run_inference_on_frame(state, frame, frame_id)

            time.sleep(0.001)

    def _run_inference_on_frame(self, state: DeviceTrackingState, frame: np.ndarray, frame_id: int) -> None:
        start_t = time.perf_counter()
        h, w = frame.shape[:2]
        scale = 1.0
        if max(h, w) > self.max_inference_size:
            scale = self.max_inference_size / float(max(h, w))
            new_w, new_h = int(w * scale), int(h * scale)
            infer_frame = cv2.resize(frame, (new_w, new_h))
        else:
            infer_frame = frame

        scale_w = infer_frame.shape[1] / float(w)
        scale_h = infer_frame.shape[0] / float(h)

        new_boxes: list[dict] = []

        try:
            with self._model_lock:
                results = self._model.predict(
                    infer_frame,
                    classes=[0],
                    imgsz=self.max_inference_size,
                    verbose=False
                )

            if results and len(results) > 0:
                res = results[0]
                if state.tracker is None:
                    state.tracker = self._create_tracker()

                if state.tracker is not None:
                    try:
                        tracks = state.tracker.update(res)
                        if tracks is not None and len(tracks) > 0:
                            for trk in tracks:
                                if len(trk) >= 6:
                                    x1, y1, x2, y2, tid, conf = trk[:6]
                                    box_x1 = int(x1 / scale_w)
                                    box_y1 = int(y1 / scale_h)
                                    box_x2 = int(x2 / scale_w)
                                    box_y2 = int(y2 / scale_h)
                                    new_boxes.append({
                                        "bbox": (box_x1, box_y1, box_x2, box_y2),
                                        "track_id": int(tid),
                                        "conf": float(conf)
                                    })
                    except Exception as trk_err:
                        pass

                # Fallback to direct detection boxes if tracker yielded no boxes
                if not new_boxes and hasattr(res, "boxes") and res.boxes is not None:
                    boxes = res.boxes
                    for i in range(len(boxes)):
                        xyxy = boxes.xyxy[i].cpu().numpy()
                        conf = float(boxes.conf[i].cpu().numpy())
                        tid = int(boxes.id[i].cpu().numpy()) if (boxes.id is not None and len(boxes.id) > i) else (i + 1)
                        box_x1 = int(xyxy[0] / scale_w)
                        box_y1 = int(xyxy[1] / scale_h)
                        box_x2 = int(xyxy[2] / scale_w)
                        box_y2 = int(xyxy[3] / scale_h)
                        new_boxes.append({
                            "bbox": (box_x1, box_y1, box_x2, box_y2),
                            "track_id": tid,
                            "conf": conf
                        })

            duration = round((time.perf_counter() - start_t) * 1000.0, 1)
            with state.lock:
                state.cached_boxes = new_boxes
                state.inference_ms = duration
                state.last_processed_frame_id = frame_id

        except Exception as e:
            print(f"[TRACKER] Inference exception on device={state.device_id}: {e}")

    def process_frame(self, device_id: str, frame: np.ndarray, frame_id: int) -> np.ndarray:
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return frame

        state = self._get_device_state(device_id)
        if not state.enabled or self._model is None:
            return frame

        # Submit latest frame to background AI worker (unblocked)
        self.submit_frame(device_id, frame, frame_id)

        now = time.time()
        elapsed = now - state.last_frame_time
        if elapsed > 0:
            current_fps = 1.0 / elapsed
            state.fps = round(0.8 * state.fps + 0.2 * current_fps, 1) if state.fps > 0 else round(current_fps, 1)
        state.last_frame_time = now

        # Draw current cached tracking boxes directly onto NEWEST frame image
        out_frame = frame.copy()
        h, w = out_frame.shape[:2]

        with state.lock:
            boxes_to_draw = list(state.cached_boxes)
            inference_ms = state.inference_ms

        for box in boxes_to_draw:
            x1, y1, x2, y2 = box["bbox"]
            tid = box["track_id"]
            conf = box["conf"]

            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w - 1, x2))
            y2 = max(0, min(h - 1, y2))

            # Bounding box
            cv2.rectangle(out_frame, (x1, y1), (x2, y2), (150, 200, 0), 2)

            # Label text
            label_str = f"Human #{tid} | {int(conf * 100)}%"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(label_str, font, font_scale, thickness)

            label_y = max(y1 - 6, text_h + 6)
            cv2.rectangle(
                out_frame,
                (x1, label_y - text_h - 4),
                (x1 + text_w + 6, label_y + baseline),
                (150, 200, 0),
                -1
            )
            cv2.putText(
                out_frame,
                label_str,
                (x1 + 3, label_y - 2),
                font,
                font_scale,
                (0, 0, 0),
                thickness,
                cv2.LINE_AA
            )

        # Stats Header Overlay
        num_humans = len(boxes_to_draw)
        stats_line = f"Humans: {num_humans} | Tracking: ON | FPS: {state.fps} | AI: {inference_ms}ms"

        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        (tw, th), baseline = cv2.getTextSize(stats_line, font, scale, 1)

        cv2.rectangle(out_frame, (8, 8), (18 + tw, 14 + th + baseline), (20, 20, 30), -1)
        cv2.rectangle(out_frame, (8, 8), (18 + tw, 14 + th + baseline), (150, 200, 0), 1)
        cv2.putText(out_frame, stats_line, (13, 12 + th), font, scale, (0, 230, 160), 1, cv2.LINE_AA)

        return out_frame


human_tracker = HumanTracker()
