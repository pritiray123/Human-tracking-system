from __future__ import annotations
import asyncio
import json
import struct
import time
import uuid
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.camera.remote import RemoteCamera
from backend.devices.registry import registry

router = APIRouter()

_sessions: Dict[str, Set[WebSocket]] = {}
_ws_session: Dict[WebSocket, str] = {}
_ws_device_id: Dict[WebSocket, str] = {}
_ws_role: Dict[WebSocket, str] = {}
_connections: Dict[str, WebSocket] = {}


async def _delayed_remove_device(device_id: str, old_ws: WebSocket) -> None:
    print(f"[HTS GracePeriod] Starting 5s grace period for device '{device_id}'")
    await asyncio.sleep(5.0)

    current_ws = _connections.get(device_id)
    if current_ws is None or current_ws == old_ws:
        cam = registry.get(device_id)
        if cam:
            cam.mark_disconnected()
        registry.remove(device_id)
        print(f"[HTS GracePeriod] Grace period expired. Removed device '{device_id}' from registry.")
    else:
        print(f"[HTS GracePeriod] Device '{device_id}' reconnected during grace period. Preserving registry.")


@router.websocket("/ws/signaling")
async def websocket_signaling_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    conn_id = uuid.uuid4().hex[:6]
    peer_ip = websocket.client.host if websocket.client else "unknown"
    print(f"[HTS WS {conn_id}] Connected from {peer_ip}")

    current_device_id: str | None = None
    is_explicit_leave: bool = False
    last_log_time = 0.0

    try:
        while True:
            try:
                msg_raw = await websocket.receive()
                msg_type_raw = msg_raw.get("type")

                if msg_type_raw == "websocket.disconnect":
                    print(f"[HTS WS {conn_id}] Received disconnect event from {peer_ip}")
                    break

                data = {}
                if "text" in msg_raw and msg_raw["text"]:
                    data["text"] = msg_raw["text"]
                if "bytes" in msg_raw and msg_raw["bytes"]:
                    data["bytes"] = msg_raw["bytes"]

                if not data:
                    continue

                if data.get("text"):
                    try:
                        msg = json.loads(data["text"])
                    except json.JSONDecodeError:
                        continue

                    msg_type = msg.get("type")

                    if msg_type == "ping":
                        try:
                            await websocket.send_text(json.dumps({"type": "pong"}))
                        except Exception:
                            pass
                        continue

                    if msg_type == "time_sync":
                        client_ts = msg.get("client_ts", 0.0)
                        server_ts = time.time()
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "time_sync_ack",
                                "client_ts": client_ts,
                                "server_ts": server_ts
                            }))
                        except Exception:
                            pass
                        continue

                    session_id = msg.get("sessionId") or "default"
                    role = msg.get("role", "viewer")
                    dev_id = msg.get("deviceId")
                    dev_name = msg.get("deviceName", "Remote Camera")

                    source_type = msg.get("sourceType") or msg.get("source_type") or "camera"
                    source_name = msg.get("sourceName") or msg.get("source_name") or "phone_camera"
                    playback_state = msg.get("playbackState") or msg.get("playback_state") or ("PLAYING" if source_type == "video" else "STREAMING")

                    if msg_type == "join":
                        if session_id not in _sessions:
                            _sessions[session_id] = set()
                        _sessions[session_id].add(websocket)
                        _ws_session[websocket] = session_id
                        _ws_role[websocket] = role

                        if role == "streamer":
                            if dev_id:
                                current_device_id = dev_id
                                _ws_device_id[websocket] = dev_id
                                _connections[dev_id] = websocket

                                existing_cam = registry.get(dev_id)
                                if isinstance(existing_cam, RemoteCamera):
                                    existing_cam._is_open = True
                                    existing_cam.label = dev_name
                                    existing_cam.source_type = source_type
                                    existing_cam.source_name = source_name
                                    existing_cam.playback_state = playback_state
                                    print(f"[HTS WS {conn_id}] Streamer '{dev_name}' ({dev_id}) re-attached active socket (Source: {source_type}).")
                                else:
                                    cam = RemoteCamera(dev_id, dev_name)
                                    cam.source_type = source_type
                                    cam.source_name = source_name
                                    cam.playback_state = playback_state
                                    cam.open()
                                    registry.add(cam)
                                    print(f"[HTS WS {conn_id}] Streamer '{dev_name}' ({dev_id}) joined session '{session_id}' (Source: {source_type})")
                            else:
                                current_device_id = uuid.uuid4().hex[:8]
                                _ws_device_id[websocket] = current_device_id
                                _connections[current_device_id] = websocket
                                cam = RemoteCamera(current_device_id, dev_name)
                                cam.source_type = source_type
                                cam.source_name = source_name
                                cam.playback_state = playback_state
                                cam.open()
                                registry.add(cam)

                        print(f"[HTS WS {conn_id}] {role.capitalize()} joined session '{session_id}' from {peer_ip}")

                        await _broadcast_session(session_id, {
                            "type": "peer-joined",
                            "sessionId": session_id,
                            "role": role,
                            "deviceId": current_device_id or dev_id
                        })

                    elif msg_type == "update_metadata":
                        target_dev_id = current_device_id or dev_id
                        if target_dev_id:
                            cam = registry.get(target_dev_id)
                            if isinstance(cam, RemoteCamera):
                                if dev_name:
                                    cam.label = dev_name
                                if "sourceType" in msg or "source_type" in msg:
                                    cam.source_type = source_type
                                if "sourceName" in msg or "source_name" in msg:
                                    cam.source_name = source_name
                                if "playbackState" in msg or "playback_state" in msg:
                                    cam.playback_state = playback_state
                                print(f"[HTS WS {conn_id}] Updated device '{target_dev_id}' metadata: label='{cam.label}', source_type='{cam.source_type}', state='{cam.playback_state}'")

                    elif msg_type in ("offer", "answer", "candidate", "ice-candidate"):
                        payload = {
                            "type": "ice-candidate" if msg_type == "candidate" else msg_type,
                            "sessionId": session_id,
                            "sdp": msg.get("sdp"),
                            "candidate": msg.get("candidate"),
                            "deviceId": dev_id,
                            "deviceName": dev_name
                        }
                        await _notify_session(session_id, websocket, payload)

                    elif msg_type == "video_control":
                        print(f"[HTS WS {conn_id}] Relay video_control '{msg.get('action')}' for device '{dev_id}'")
                        await _notify_session(session_id, websocket, msg)


                    elif msg_type == "leave":
                        print(f"[HTS WS {conn_id}] Received explicit client leave signal from device '{current_device_id or dev_id}'")
                        is_explicit_leave = True
                        break

                elif data.get("bytes"):
                    receive_ts = time.time()
                    raw_bytes = data["bytes"]
                    if not raw_bytes:
                        continue

                    if not current_device_id:
                        current_device_id = uuid.uuid4().hex[:8]
                        _ws_device_id[websocket] = current_device_id
                        _connections[current_device_id] = websocket
                        cam = RemoteCamera(current_device_id, f"Remote ({peer_ip})")
                        cam.open()
                        registry.add(cam)

                    cam = registry.get(current_device_id)
                    if cam is not None:
                        capture_ts = 0.0
                        jpeg_bytes = raw_bytes

                        if len(raw_bytes) > 12 and raw_bytes[:4] == b"HTS1":
                            try:
                                capture_ts = struct.unpack("<d", raw_bytes[4:12])[0]
                                jpeg_bytes = raw_bytes[12:]
                            except Exception as header_err:
                                print(f"[HTS WS {conn_id}] Header unpack warning: {header_err}")

                        cam.push_jpeg_bytes(jpeg_bytes, capture_ts=capture_ts)
                        store_ts = time.time()

                        curr = time.time()
                        if curr - last_log_time >= 3.0:
                            last_log_time = curr
                            kb_size = round(len(raw_bytes) / 1024.0, 1)
                            print(f"[HTS LATENCY] Device '{current_device_id}' ({cam.label}) | Size: {kb_size} KB")

            except Exception as msg_err:
                print(f"[HTS WS {conn_id}] Non-fatal message processing error from {peer_ip}: {repr(msg_err)}")
                continue

    except Exception as outer_err:
        print(f"[HTS WS {conn_id}] Outer loop exception for {peer_ip}: {repr(outer_err)}")
    finally:
        session_id = _ws_session.pop(websocket, None)
        dev_id = _ws_device_id.pop(websocket, None)
        _ws_role.pop(websocket, None)

        if session_id and session_id in _sessions:
            _sessions[session_id].discard(websocket)
            if dev_id:
                await _broadcast_session(session_id, {
                    "type": "peer-left",
                    "sessionId": session_id,
                    "deviceId": dev_id
                })
            if not _sessions[session_id]:
                _sessions.pop(session_id, None)

        if dev_id:
            current_ws = _connections.get(dev_id)
            if current_ws == websocket:
                _connections.pop(dev_id, None)
            cam = registry.get(dev_id)
            if cam:
                cam.mark_disconnected()

            if is_explicit_leave:
                registry.remove(dev_id)
                print(f"[HTS Device] Immediately removed device from registry on explicit client leave: '{dev_id}'")
            else:
                asyncio.create_task(_delayed_remove_device(dev_id, websocket))


async def _notify_session(session_id: str, sender: WebSocket, payload: dict) -> None:
    peers = _sessions.get(session_id, set())
    msg_str = json.dumps(payload)
    for ws in list(peers):
        if ws != sender:
            try:
                await ws.send_text(msg_str)
            except Exception:
                pass


async def _broadcast_session(session_id: str, payload: dict) -> None:
    peers = _sessions.get(session_id, set())
    msg_str = json.dumps(payload)
    for ws in list(peers):
        try:
            await ws.send_text(msg_str)
        except Exception:
            pass


async def send_video_control(device_id: str, action: str, params: dict | None = None) -> bool:
    ws = _connections.get(device_id)
    if ws is not None:
        try:
            payload = {
                "type": "video_control",
                "action": action,
                "deviceId": device_id,
            }
            if params:
                payload.update(params)
            await ws.send_text(json.dumps(payload))
            print(f"[HTS Signaling] Sent video_control '{action}' directly to device '{device_id}'")
            return True
        except Exception as e:
            print(f"[HTS Signaling] Exception sending video_control to '{device_id}': {e}")
    return False


async def close_device(device_id: str, reason: str = "Disconnected by dashboard") -> None:
    ws = _connections.get(device_id)
    if ws is not None:
        try:
            print(f"[HTS Signaling] Sending force_disconnect to device '{device_id}' (Reason: {reason})")
            await ws.send_text(json.dumps({
                "type": "force_disconnect",
                "reason": reason,
                "deviceId": device_id
            }))
            await asyncio.sleep(0.05)
            await ws.close()
        except Exception as e:
            print(f"[HTS Signaling] Exception sending force_disconnect to '{device_id}': {e}")
        finally:
            _connections.pop(device_id, None)

    cam = registry.get(device_id)
    if cam:
        cam.mark_disconnected()
    registry.remove(device_id)
    print(f"[HTS Device] Removed from registry on force disconnect: '{device_id}'")

