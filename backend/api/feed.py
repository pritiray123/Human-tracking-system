from __future__ import annotations
import asyncio
import base64
import json
import time
import cv2
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import backend.config as config
from backend.devices.registry import registry

router  = APIRouter()
_clients: set[WebSocket] = set()


@router.websocket("/ws/feed")
async def camera_feed(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        _clients.discard(websocket)


async def start_broadcaster() -> None:
    loop      = asyncio.get_event_loop()
    prev_time = time.time()
    target_fps = 30.0
    frame_interval = 1.0 / target_fps

    while True:
        if not _clients:
            await asyncio.sleep(0.1)
            continue

        active = registry.get_active()

        if active is None:
            msg = json.dumps({"type": "no_camera"})
            await _broadcast(msg)
            await asyncio.sleep(0.5)
            continue

        ok, frame = await loop.run_in_executor(None, active.read)

        if not ok:
            if frame is None:
                await asyncio.sleep(0.033)
                continue
            else:
                print(f"[Feed] Fatal camera failure: {active.label}")
                registry.remove(active.device_id)
                await asyncio.sleep(0.1)
                continue

        encode_params = [cv2.IMWRITE_JPEG_QUALITY, config.FEED_JPEG_QUALITY]
        _, buf = cv2.imencode(".jpg", frame, encode_params)
        b64 = base64.b64encode(buf.tobytes()).decode("ascii")

        curr      = time.time()
        elapsed   = curr - prev_time
        fps       = round(1.0 / elapsed, 1) if elapsed > 0 else 0.0
        prev_time = curr

        msg = json.dumps({
            "type":  "frame",
            "frame": b64,
            "label": active.label,
            "fps":   fps,
        })

        await _broadcast(msg)

        sleep_time = max(0.001, frame_interval - elapsed) if elapsed < frame_interval else 0.001
        await asyncio.sleep(sleep_time)


async def _broadcast(msg: str) -> None:
    dead: set[WebSocket] = set()
    for ws in list(_clients):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _clients -= dead
