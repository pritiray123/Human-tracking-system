from __future__ import annotations
import random
import string
import time
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import backend.config as config
from backend.camera.remote import RemoteCamera
from backend.devices.registry import registry
from backend.transport import ws_receiver

router = APIRouter()

_STREAMER_PATH = (
    Path(__file__).parent.parent
    / "transport"
    / "static"
    / "streamer.html"
)


def _generate_session_id() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=6))


@router.get("/session/new")
@router.post("/session/new")
def create_session(request: Request) -> dict:
    session_id = _generate_session_id()
    host = config.LOCAL_IP
    port = config.BACKEND_PORT

    base_streamer = (
        config.PUBLIC_STREAMER_URL
        or f"http://{host}:{port}/api/streamer"
    )
    streamer_link = f"{base_streamer}?session={session_id}"

    return {
        "session_id": session_id,
        "streamer_link": streamer_link,
    }


@router.get("/info")
def get_info(request: Request) -> dict:
    host = config.LOCAL_IP
    port = config.BACKEND_PORT
    streamer_url = f"http://{host}:{port}/api/streamer"

    ice_servers = [
        {
            "urls": [
                config.STUN_URL,
                config.STUN_URL_ALT,
            ]
        }
    ]

    if config.TURN_URL:
        turn_urls = [
            url.strip()
            for url in config.TURN_URL.split(",")
            if url.strip()
        ]
        turn_entry = {
            "urls": (
                turn_urls
                if len(turn_urls) > 1
                else turn_urls[0]
            )
        }
        if config.TURN_USERNAME:
            turn_entry["username"] = config.TURN_USERNAME
        if config.TURN_PASSWORD:
            turn_entry["credential"] = config.TURN_PASSWORD
        ice_servers.append(turn_entry)

    return {
        "streamer_url": streamer_url,
        "public_streamer_url": config.PUBLIC_STREAMER_URL,
        "signaling_url": config.SIGNALING_URL,
        "local_ip": host,
        "port": port,
        "protocol": "http",
        "ice_servers": ice_servers,
        "force_turn": config.FORCE_TURN,
        "turn_configured": bool(config.TURN_URL),
        "default_width": config.DEFAULT_FRAME_WIDTH,
        "default_height": config.DEFAULT_FRAME_HEIGHT,
        "default_fps": config.DEFAULT_TARGET_FPS,
        "jpeg_quality": config.FEED_JPEG_QUALITY,
    }


@router.get("/devices")
def get_devices() -> list[dict]:
    res = []
    for device_id, cam, is_active in registry.list_devices():
        dev_type = (
            "local"
            if device_id.startswith("local:")
            else "remote"
        )
        has_frame = (
            getattr(cam, "_latest_frame", None) is not None
            or getattr(cam, "_latest_jpeg_bytes", None) is not None
        )

        if cam.is_open:
            if dev_type == "local" or has_frame:
                status = "STREAMING"
            else:
                status = "SIGNALING"
        else:
            status = "DISCONNECTED"

        res.append(
            {
                "id": device_id,
                "label": cam.label,
                "width": cam.width,
                "height": cam.height,
                "is_open": cam.is_open,
                "is_active": is_active,
                "type": dev_type,
                "status": status,
                "latency_ms": getattr(
                    cam,
                    "latency_ms",
                    0.0
                ),
            }
        )
    return res


@router.post("/devices/{device_id}/active")
def set_active_device(device_id: str) -> dict:
    print(f"[HTS Backend] Set active device request for: '{device_id}'")
    if not registry.set_active(device_id):
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    print(f"[HTS Backend] Active device updated to: '{registry._active_id}'")
    return {
        "status": "ok",
        "active": device_id,
    }


@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(device_id: str) -> dict:
    print(f"[HTS REST] Authoritative disconnect requested for device '{device_id}'")
    await ws_receiver.close_device(device_id, reason="Disconnected by dashboard user")
    cam = registry.get(device_id)
    if cam:
        try:
            cam.release()
        except Exception as e:
            print(f"[HTS REST] Exception releasing camera '{device_id}': {e}")
        registry.remove(device_id)
        print(f"[HTS REST] Removed '{device_id}' from registry")
    return {
        "status": "ok",
        "disconnected": device_id
    }


@router.get("/stream/active")
def stream_active(
    dev: Optional[str] = None,
    t: Optional[str] = None
):
    def generate():
        last_sent_bytes: bytes | None = None
        last_log_time = 0.0
        while True:
            if dev:
                active = registry.get(dev)
            else:
                active = registry.get_active()

            if active is None:
                time.sleep(0.033)
                continue

            if isinstance(active, RemoteCamera):
                ok, jpeg_bytes, cap_ts = active.get_latest_jpeg()
                if ok and jpeg_bytes and jpeg_bytes != last_sent_bytes:
                    send_start = time.time()
                    last_sent_bytes = jpeg_bytes

                    if cap_ts > 0 and send_start - last_log_time >= 3.0:
                        last_log_time = send_start
                        cap_to_yield_ms = round((send_start - cap_ts) * 1000.0, 1)

                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        + b"Content-Length: "
                        + str(len(jpeg_bytes)).encode("ascii")
                        + b"\r\n\r\n"
                        + jpeg_bytes
                        + b"\r\n"
                    )
                    time.sleep(0.005)
                else:
                    time.sleep(0.01)
                continue

            ok, frame = active.read()
            if not ok or frame is None:
                time.sleep(0.033)
                continue

            if isinstance(frame, bytes):
                np_frame = np.frombuffer(frame, dtype=np.uint8)
                frame = cv2.imdecode(
                    np_frame,
                    cv2.IMREAD_COLOR
                )
                if frame is None:
                    time.sleep(0.033)
                    continue

            ok_jpg, buf = cv2.imencode(
                ".jpg",
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    config.FEED_JPEG_QUALITY
                ]
            )
            if not ok_jpg:
                time.sleep(0.033)
                continue

            jpeg_bytes = buf.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                + b"Content-Length: "
                + str(len(jpeg_bytes)).encode("ascii")
                + b"\r\n\r\n"
                + jpeg_bytes
                + b"\r\n"
            )
            time.sleep(0.033)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )


@router.get(
    "/streamer",
    response_class=HTMLResponse,
)
def serve_streamer() -> HTMLResponse:
    try:
        html = _STREAMER_PATH.read_text(
            encoding="utf-8"
        )
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="streamer.html not found",
        )

    if config.PUBLIC_URL:
        public_host = (
            config.PUBLIC_URL
            .replace("https://", "")
            .replace("http://", "")
            .rstrip("/")
        )
        html = html.replace(
            "{{WS_HOST}}",
            public_host,
        )
        html = html.replace(
            "{{WS_PORT}}",
            "",
        )
    else:
        html = html.replace(
            "{{WS_HOST}}",
            config.LOCAL_IP,
        )
        html = html.replace(
            "{{WS_PORT}}",
            str(config.BACKEND_PORT),
        )

    return HTMLResponse(content=html)