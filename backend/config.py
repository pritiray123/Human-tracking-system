import os
import socket
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
_ENV_FILE     = _PROJECT_ROOT / ".env"

if _ENV_FILE.exists():
    try:
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if len(val) >= 2 and val[0] in ("'", '"') and val[-1] == val[0]:
                    val = val[1:-1]
                os.environ[key] = val
    except Exception as e:
        print(f"[HTS Config] Error loading .env: {e}")

def _get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


BACKEND_PORT: int = 8000
CAMERA_INDEX_CANDIDATES: list[int] = [0, 1, 2, 3, 4]
MAX_FRAME_QUEUE: int = 1
REMOTE_READ_TIMEOUT: float = 0.05
FEED_JPEG_QUALITY: int = 65

DEFAULT_FRAME_WIDTH: int = 640
DEFAULT_FRAME_HEIGHT: int = 480
DEFAULT_TARGET_FPS: int = 24

LOCAL_IP: str = _get_local_ip()
HTTPS_ENABLED: bool = False

raw_public = (os.environ.get("PUBLIC_URL") or os.environ.get("VITE_API_BASE_URL") or "").strip().rstrip("/")
if raw_public:
    while raw_public.startswith("https://") or raw_public.startswith("http://"):
        if raw_public.startswith("https://"):
            raw_public = raw_public[8:]
        elif raw_public.startswith("http://"):
            raw_public = raw_public[7:]
    PUBLIC_URL = "https://" + raw_public.strip().rstrip("/")
else:
    PUBLIC_URL = ""

raw_signaling = (os.environ.get("SIGNALING_URL") or os.environ.get("VITE_WS_URL") or "").strip().rstrip("/")
if raw_signaling:
    while raw_signaling.startswith("wss://") or raw_signaling.startswith("ws://"):
        if raw_signaling.startswith("wss://"):
            raw_signaling = raw_signaling[6:]
        elif raw_signaling.startswith("ws://"):
            raw_signaling = raw_signaling[5:]
    SIGNALING_URL = "wss://" + raw_signaling.strip().rstrip("/")
elif PUBLIC_URL:
    clean_host = PUBLIC_URL.replace("https://", "").replace("http://", "").rstrip("/")
    SIGNALING_URL = f"wss://{clean_host}/ws/signaling"
else:
    SIGNALING_URL = ""

STREAMER_URL: str = f"http://{LOCAL_IP}:{BACKEND_PORT}/api/streamer"
PUBLIC_STREAMER_URL: str = f"{PUBLIC_URL}/api/streamer" if PUBLIC_URL else ""

STUN_URL: str = os.environ.get("STUN_URL") or os.environ.get("STUN_SERVER") or "stun:stun.l.google.com:19302"
STUN_URL_ALT: str = os.environ.get("STUN_URL_ALT") or os.environ.get("STUN_SERVER_ALT") or "stun:stun1.l.google.com:19302"

TURN_URL: str = os.environ.get("TURN_URL") or os.environ.get("TURN_SERVER") or "turn:openrelay.metered.ca:80,turn:openrelay.metered.ca:443"
TURN_USERNAME: str = os.environ.get("TURN_USERNAME") or "openrelayproject"
TURN_PASSWORD: str = os.environ.get("TURN_PASSWORD") or "openrelayproject"

FORCE_TURN: bool = os.environ.get("FORCE_TURN", "false").lower() in ("true", "1", "yes")

print(f"[HTS Config] LOCAL_IP = {LOCAL_IP}:{BACKEND_PORT}")
print(f"[HTS Config] PUBLIC_URL = {PUBLIC_URL or '(local mode)'}")
print(f"[HTS Config] SIGNALING_URL = {SIGNALING_URL or '(local default)'}")
print(f"[HTS Config] STUN/TURN configured = True ({STUN_URL}, {TURN_URL})")
