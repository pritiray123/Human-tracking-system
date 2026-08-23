# Human Tracking System (HTS)
### Complete Step-by-Step Implementation Guide with Line-by-Line Code Explanation

> **Rule:** Every meaningful line of code is explained immediately after the complete code block.
> Copy the complete code first, then read the explanation to understand every line.

---

## Table of Contents

- [Part 1 — Current Project](#part-1--current-project)
- [Part 2 — Proposed Project Structure](#part-2--proposed-project-structure)
- [Part 3 — Step-by-Step Implementation Guide](#part-3--step-by-step-implementation-guide)
- [Part 4 — Architecture and Data Flow](#part-4--architecture-and-data-flow)
- [Part 5 — Dependencies](#part-5--dependencies)
- [Part 6 — Current Status](#part-6--current-status)
- [Part 7 — Fixes & Architecture Updates](#part-7--fixes--architecture-updates)

---

# Part 1 — Current Project

---

## Existing File: `phase1_camera/camera_capture.py`

**Status:** EXISTING — do not modify.

### Complete Code

```python
import cv2
import time
camera_index_candidates = [1, 0, 2, 3, 4]


def _open_camera():
    for camera_index in camera_index_candidates:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        time.sleep(1)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 0.0
            print(f"camera opened:{width}x{height} @ {fps:.1f} FPS (index {camera_index})")
            return cap, width, height, fps

        cap.release()

    raise RuntimeError("can not open any camera index")


cap, width, height, fps = _open_camera()


def readframe(cap):
    success, frame = cap.read()
    return success, frame


def release_camera(cap):
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("camera released.Application Closed")
```

### Understand the Code Line by Line

---

```python
import cv2
```

**What is written?** The `import` keyword followed by the module name `cv2`.

**What does it mean?** Loads the OpenCV library into the program. After this line, every OpenCV function is available under the prefix `cv2.` — for example, `cv2.VideoCapture`, `cv2.imshow`, `cv2.imread`.

**Why is it needed?** OpenCV is the only Python library that can talk to camera hardware on Windows, read raw video frames, and convert them into NumPy arrays.

**What if removed?** `NameError: name 'cv2' is not defined` the moment anything tries to call `cv2.VideoCapture()`.

---

```python
import time
```

**What is written?** Imports Python's built-in `time` module.

**What does it mean?** Gives access to `time.sleep()`, which pauses execution for a specified number of seconds.

**Why is it needed?** `time.sleep(1)` inside `_open_camera()` waits one second after opening a camera before reading its properties. Without this pause, some webcam drivers report 0×0 resolution because the hardware has not finished initialising.

---

```python
camera_index_candidates = [1, 0, 2, 3, 4]
```

**What is written?** A module-level variable `camera_index_candidates` assigned a Python list of integers.

**What does it mean?** This list holds the camera device indices to try when searching for a working webcam. Index 0, 1, 2 etc. correspond to `/dev/video0`, `/dev/video1` on Linux, or DirectShow device 0, 1, 2 on Windows.

**Why is it needed?** On many Windows laptops, an external USB webcam is enumerated as index 1 while the built-in webcam is index 0. The order `[1, 0, 2, 3, 4]` means the external camera is tried first. If no external camera exists, index 0 (built-in) is tried next.

**What if changed to `[0]`?** Only device index 0 is tried. On some laptops this fails because the first USB webcam is at index 1.

---

```python
def _open_camera():
```

**What is written?** A function definition. The leading underscore `_` is a Python naming convention meaning "this is a private helper — do not call it from outside this module."

**What does it mean?** Defines a function that will scan available camera indices and return the first working one.

**Why is it needed?** Opening a camera requires trying multiple indices. Putting this logic in a function keeps it separate from the rest of the code.

---

```python
    for camera_index in camera_index_candidates:
```

**What is written?** A `for` loop iterating over the list `[1, 0, 2, 3, 4]`.

**What does it mean?** On each iteration, `camera_index` takes the next value from the list: first 1, then 0, then 2, and so on.

**Why is it needed?** We do not know which index works on this machine. The loop tries each one until it finds one that opens successfully.

---

```python
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
```

**What is written?**
- `cap` — variable that will hold the camera handle.
- `cv2.VideoCapture(...)` — OpenCV function that opens a video capture device.
- `camera_index` — the integer index of the device to open (from the loop above).
- `cv2.CAP_DSHOW` — a constant telling OpenCV to use the Windows DirectShow API.

**What does it mean?** Asks OpenCV to open the camera hardware at the given index using the DirectShow driver.

**Why `cv2.CAP_DSHOW`?** OpenCV on Windows tries the Media Foundation API by default, which is slow to initialise and sometimes fails silently for USB webcams. DirectShow (`CAP_DSHOW`) is the older but more reliable Windows camera API.

**What if `cv2.CAP_DSHOW` is removed?** `cv2.VideoCapture(camera_index)` uses the default backend. Some webcams may fail to open, freeze during initialisation, or report wrong FPS.

---

```python
        time.sleep(1)
```

**What is written?** Calls `time.sleep()` with the argument `1`, pausing the program for one second.

**Why is it needed?** After calling `cv2.VideoCapture()`, the camera driver begins its hardware initialisation sequence in the background. Immediately calling `.isOpened()` may return `True` while `.get(cv2.CAP_PROP_FRAME_WIDTH)` still returns 0 because the driver has not finished. The 1-second pause allows the hardware to settle.

**What if removed?** On some webcams, `width` and `height` will be 0, causing a window of size 0×0. The application appears to start but no video is shown.

---

```python
        if cap.isOpened():
```

**What is written?** Calls the `.isOpened()` method on the `cap` object and checks if it returns `True`.

**What does it mean?** `.isOpened()` returns `True` if OpenCV successfully established a connection to the camera hardware. It returns `False` if the device does not exist or is already in use by another application.

**Why is it needed?** Without this check, we would try to read frames from a camera that never opened, getting errors or empty frames.

---

```python
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
```

**What is written?**
- `cap.get(cv2.CAP_PROP_FRAME_WIDTH)` — reads the width property from the camera.
- `int(...)` — converts the float that `cap.get()` always returns to an integer.
- Same pattern for height.

**Why `int()`?** `cap.get()` always returns a Python `float`, even for pixel dimensions. `int(1280.0)` becomes `1280`. Without `int()`, you get `1280.0` which causes type errors when passed to functions expecting integer pixel counts.

---

```python
            fps = cap.get(cv2.CAP_PROP_FPS)
```

**What is written?** Reads the camera's reported frames-per-second value.

**Why not `int()` here?** FPS can legitimately be fractional (e.g., 29.97 for NTSC video). We keep it as a float.

---

```python
            if fps <= 0:
                fps = 0.0
```

**What is written?** Checks if the camera reported an invalid FPS and replaces it with `0.0`.

**Why is it needed?** Some cameras report `-1.0` or `0` for FPS when the driver cannot determine it. A negative FPS would look wrong in any display output. `0.0` is the safe sentinel value meaning "unknown."

---

```python
            return cap, width, height, fps
```

**What is written?** Returns four values as a Python tuple: the camera handle, frame width, frame height, and FPS.

**What does it mean?** This ends the function immediately with a successful result. The `for` loop stops. No other camera indices are tried.

**What happens next?** The caller `cap, width, height, fps = _open_camera()` receives all four values and assigns each to a named variable.

---

```python
        cap.release()
```

**What is written?** Calls `.release()` on the camera handle that failed to open.

**Why is it needed?** Even a camera that fails `.isOpened()` may have partially allocated OS resources (device handles, memory buffers). Calling `.release()` returns those resources to the OS before trying the next index.

**What if removed?** On some systems, the OS locks the camera device even on a failed open. The next index may also fail because the device appears occupied.

---

```python
    raise RuntimeError("can not open any camera index")
```

**What is written?** After the `for` loop finishes without returning, this line raises a `RuntimeError` exception.

**What does it mean?** Every index in `camera_index_candidates` was tried and none succeeded. The program cannot continue without a camera, so an error is raised.

**Why `RuntimeError`?** This is a standard Python exception for situations where the program reaches an impossible runtime state — not a programming bug, but an environment failure.

**What if removed?** The function would return `None` implicitly. The line `cap, width, height, fps = _open_camera()` would raise `TypeError: cannot unpack non-iterable NoneType object` — a confusing error with no indication of what actually went wrong.

---

```python
cap, width, height, fps = _open_camera()
```

**What is written?** This line is at module level — outside any function. It calls `_open_camera()` and unpacks the four return values.

**What does it mean?** This line executes **the moment Python imports this file**. The camera opens as soon as `from phase1_camera.camera_capture import cap` runs.

**Why at module level?** The original design treats camera access as a module-level resource — open once, share everywhere. It is simple but not extensible (only one camera, and it opens even in tests).

**What if moved inside a function?** The caller would need to explicitly call `open()` before reading frames. That is exactly what the upgraded `LocalCamera` class in Step 4 does.

---

```python
def readframe(cap):
    success, frame = cap.read()
    return success, frame
```

**`cap.read()`** — calls the internal OpenCV frame read. Returns two values:
- `success` — `True` if a frame was read, `False` if the camera failed or ended.
- `frame` — a NumPy `ndarray` of shape `(height, width, 3)`, dtype `uint8`, channels in BGR order. `None` if `success` is `False`.

**Why wrap it?** The function exists so `camera_app.py` never calls `cap.read()` directly. If the camera is replaced (network stream, file), only this wrapper changes.

---

```python
def release_camera(cap):
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("camera released.Application Closed")
```

**`if cap is not None`** — guards against releasing a `None` handle (which would crash). `cap` could theoretically be `None` if `_open_camera()` was patched to return `None` in tests.

**`cap.release()`** — tells the OS to return the camera device. After this, the camera LED turns off and other applications can open the camera.

**`cv2.destroyAllWindows()`** — closes all OpenCV-managed windows. Without this, the window stays visible as a frozen image.

---

## Existing File: `phase1_camera/camera_app.py`

**Status:** EXISTING — do not modify.

### Complete Code

```python
import cv2
import time

from phase1_camera.camera_capture import cap, height, readframe, release_camera, width

WINDOW_NAME = "HTS"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, width, height)

is_running = True
prev_time = time.time()


def window_closed(window_name):
    try:
        return cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True

try:
    while is_running:
        success, frame = readframe(cap)

        if not success:
            print("Frame read failed. Camera may have disconnected")
            is_running = False
            continue

        curr_time = time.time()
        loop_fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        cv2.putText(
            frame,
            f"fps:{loop_fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
        )
        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF

        if window_closed(WINDOW_NAME):
            is_running = False
            continue

        if key == ord("q"):
            is_running = False
finally:
    release_camera(cap)
```

### Understand the Code Line by Line

---

```python
from phase1_camera.camera_capture import cap, height, readframe, release_camera, width
```

**What is written?** A selective import — only the listed names are brought into this file's namespace.

**What does it mean?** When Python processes this line, it imports `camera_capture.py`, which immediately runs `cap, width, height, fps = _open_camera()`. By the time this import finishes, the camera is already open.

**Why selective import instead of `import camera_capture`?** So we can write `readframe(cap)` instead of `camera_capture.readframe(camera_capture.cap)` — shorter and more readable.

---

```python
WINDOW_NAME = "HTS"
```

**What is written?** A module-level constant (uppercase by Python convention) assigned the string `"HTS"`.

**Why a constant?** `WINDOW_NAME` is used in three places: `namedWindow`, `resizeWindow`, and `getWindowProperty`. If typed as a string literal in each place, a typo in one of them would cause the window to not be found. Using a constant means a typo is caught at the variable definition, not at runtime.

---

```python
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
```

**`cv2.namedWindow(name, flags)`** — creates a named GUI window.

**`cv2.WINDOW_NORMAL`** — flag that makes the window resizable by the user. The alternative `cv2.WINDOW_AUTOSIZE` creates a fixed-size window that cannot be resized.

**Why create the window before the loop?** So `cv2.resizeWindow` can be called immediately. If you call `cv2.imshow` first (without `namedWindow`), OpenCV creates a non-resizable window automatically.

---

```python
cv2.resizeWindow(WINDOW_NAME, width, height)
```

**What is written?** Sets the initial window size to match the camera's native resolution.

**`width`, `height`** — these came from the import above, set by `_open_camera()`.

**Why?** If the window starts smaller than the camera resolution, OpenCV scales the image down. Starting at native resolution gives the sharpest image immediately.

---

```python
is_running = True
```

**What is written?** A boolean flag used to control the main loop.

**Why a flag instead of `while True`?** Multiple conditions can stop the loop (camera failure, Q key, window close). A flag lets all of them set `is_running = False` without needing `break` from nested code. This makes the exit logic cleaner.

---

```python
prev_time = time.time()
```

**`time.time()`** — returns the current time as a floating-point number representing seconds since the Unix epoch (Jan 1, 1970).

**Why before the loop?** FPS is calculated as `1.0 / (current_time - previous_time)`. `prev_time` needs an initial value before the first loop iteration. If set inside the loop, the first FPS calculation would divide by a very small number (time since loop start) giving a meaningless spike.

---

```python
def window_closed(window_name):
    try:
        return cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True
```

**`cv2.getWindowProperty(name, prop)`** — reads a property of a named window.

**`cv2.WND_PROP_VISIBLE`** — the property that equals 1.0 if the window is visible, less than 1.0 if it has been closed.

**Why `< 1` instead of `== 0`?** The return value is a float and can be `-1.0` when the window does not exist. `< 1` catches both `0.0` and `-1.0`.

**`except cv2.error: return True`** — if the window has already been fully destroyed, `getWindowProperty` raises `cv2.error`. Returning `True` treats this as "window is closed" — the correct response.

**Why this function?** Pressing the X button on a window does not generate a keyboard event. Without this check, clicking X closes the visual window but the Python process keeps running, reading frames into nothing.

---

```python
        success, frame = readframe(cap)
```

**What is written?** Calls `readframe(cap)` from `camera_capture.py` and unpacks the two return values.

**`success`** — `True` if a frame was captured, `False` on camera failure.

**`frame`** — NumPy ndarray shape `(H, W, 3)` BGR, or `None` if `success` is `False`.

---

```python
        if not success:
            print("Frame read failed. Camera may have disconnected")
            is_running = False
            continue
```

**`if not success`** — checks for camera failure.

**`is_running = False`** — will cause the `while` loop to exit after this iteration.

**`continue`** — skips the rest of the loop body for this iteration. Without `continue`, the code would proceed to `cv2.putText(frame, ...)` with `frame = None`, crashing with `AttributeError`.

---

```python
        loop_fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
```

**What is written?** A conditional expression (ternary). If the time difference is greater than 0, compute FPS; otherwise return 0.

**`1.0 / (curr_time - prev_time)`** — frames per second = 1 second ÷ seconds per frame.

**Why guard `> 0`?** If two consecutive calls to `time.time()` return the same value (possible on low-resolution system clocks), division by zero would crash the program.

---

```python
        cv2.putText(frame, f"fps:{loop_fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
```

**`cv2.putText(image, text, origin, font, scale, color, thickness)`** — draws text directly on the NumPy array `frame`, modifying it in place.

**`(10, 30)`** — pixel coordinates of the bottom-left corner of the text. X=10 from left, Y=30 from top.

**`(0, 255, 0)`** — BGR colour. 0 blue, 255 green, 0 red → bright green.

**`2`** — line thickness in pixels.

**Why draw on `frame` directly?** `cv2.putText` modifies the array in place. The modified array is then passed to `cv2.imshow`. There is no separate overlay — the annotation is baked into the displayed image.

---

```python
        key = cv2.waitKey(1) & 0xFF
```

**`cv2.waitKey(1)`** — waits up to 1 millisecond for a keyboard event, then returns. This function also processes all pending OpenCV GUI events (mouse clicks, window resize, paint). Without this call, the window freezes.

**`& 0xFF`** — bitwise AND with binary `11111111`. This keeps only the lowest 8 bits of the return value. On some Linux systems with modifier keys held (Shift, Ctrl, Alt), the upper bits of the return value are set, making `key == ord('q')` fail. `& 0xFF` normalises the value across all platforms.

---

```python
        if key == ord("q"):
            is_running = False
```

**`ord("q")`** — returns the ASCII integer value of the character `"q"`, which is 113.

**Why `ord()` and not just `113`?** `ord("q")` makes the code self-documenting — readable as "if the Q key was pressed."

---

```python
finally:
    release_camera(cap)
```

**`try...finally`** — the `finally` block executes regardless of how the `try` block exits: normal loop end, `break`, `return`, or any uncaught exception (including Ctrl+C which raises `KeyboardInterrupt`).

**Why `finally` and not just after the loop?** If `KeyboardInterrupt` (Ctrl+C) is raised inside the loop, code after the `while` block does not run. Using `finally` guarantees `release_camera(cap)` always executes, returning the camera to the OS.

---

# Part 2 — Proposed Project Structure

```text
human tracking 1/
│
├── backend/
│   ├── main.py                         FastAPI app entry point
│   ├── config.py                       All constants
│   ├── camera/
│   │   ├── __init__.py
│   │   ├── base.py                     CameraSource abstract class
│   │   ├── local.py                    Local webcam implementation
│   │   └── remote.py                   Remote WebSocket camera
│   ├── devices/
│   │   ├── __init__.py
│   │   └── registry.py                 Thread-safe device store
│   ├── transport/
│   │   ├── __init__.py
│   │   ├── ws_receiver.py              Receives frames from remote browsers
│   │   └── static/
│   │       └── streamer.html           Browser page for remote devices
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                   REST endpoints
│   │   └── feed.py                     WebSocket feed to React
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       ├── services/
│       │   └── api.js
│       ├── hooks/
│       │   └── useCameraFeed.js
│       └── components/
│           ├── StatusBar.jsx
│           ├── DevicePanel.jsx
│           └── CameraFeed.jsx
│
├── phase1_camera/                      Original code — untouched
└── README.md
```

---

# Part 3 — Step-by-Step Implementation Guide

---

## Step 1 — Create the Project Layout

**Goal:** Create all folders before writing any code. Python cannot import from a folder unless it exists.

**Commands:**

```powershell
mkdir backend
mkdir backend\camera
mkdir backend\devices
mkdir backend\transport
mkdir backend\transport\static
mkdir backend\api

New-Item backend\__init__.py        -ItemType File
New-Item backend\camera\__init__.py -ItemType File
New-Item backend\devices\__init__.py -ItemType File
New-Item backend\transport\__init__.py -ItemType File
New-Item backend\api\__init__.py    -ItemType File
```

**Why `__init__.py`?** Python treats a directory as a package only when an `__init__.py` file exists inside it. Without it, `from backend.camera.local import LocalCamera` raises `ModuleNotFoundError` even if the file is there.

**After this step:** `tree /F backend` shows all folders and empty `__init__.py` files.

---

## Step 2 — Backend Configuration

**Goal:** Create a single file that holds every tunable value: ports, timeouts, quality settings, and the machine's IP address. Every other backend file imports from here.

**File:** `backend/config.py` — **NEW**

### Complete Code

```python
import socket


def _get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


BACKEND_PORT: int = 8000
CAMERA_INDEX_CANDIDATES: list[int] = [0, 1, 2, 3, 4]
MAX_FRAME_QUEUE: int = 5
REMOTE_READ_TIMEOUT: float = 0.05
FEED_JPEG_QUALITY: int = 80
LOCAL_IP: str = _get_local_ip()
```

### Understand the Code Line by Line

---

```python
import socket
```

**What is written?** Imports Python's built-in `socket` module.

**What does it mean?** `socket` gives access to low-level network operations: creating sockets, connecting to addresses, reading local network interface details.

**Why is it needed?** The `_get_local_ip()` function below needs `socket.socket()` to determine the machine's LAN IP address.

**What if removed?** `NameError: name 'socket' is not defined` on the first line of `_get_local_ip()`.

---

```python
def _get_local_ip() -> str:
```

**`def`** — begins a function definition.

**`_get_local_ip`** — the underscore prefix signals this is a private helper, not part of the module's public API.

**`-> str`** — return type annotation. Tells any code reader (and type checkers like mypy) that this function always returns a string.

---

```python
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
```

**`socket.socket(socket.AF_INET, socket.SOCK_DGRAM)`** — creates a new socket object.
- `socket.AF_INET` — use IPv4 address family.
- `socket.SOCK_DGRAM` — use UDP (datagram) protocol, not TCP.

**Why UDP and not TCP?** We are not actually sending data. We just need the OS to tell us which local interface it would use for an outgoing connection. UDP does this instantly without completing a connection handshake. TCP would need to actually connect to the remote host.

**`with ... as s`** — context manager. Automatically closes the socket when the `with` block exits, even if an exception occurs. Equivalent to calling `s.close()` in a `finally` block.

---

```python
            s.connect(("8.8.8.8", 80))
```

**`s.connect(address)`** — for a UDP socket, this does not actually send any data or complete a network handshake. It only tells the OS: "this socket intends to send to 8.8.8.8 on port 80." The OS responds by selecting the appropriate local network interface.

**`"8.8.8.8"`** — Google's DNS server. This address is always reachable by the OS routing table (even if there is no internet connection) because the routing table knows which interface to use for that destination.

**`80`** — HTTP port. Chosen arbitrarily. Any port number would work since no data is sent.

---

```python
            return s.getsockname()[0]
```

**`s.getsockname()`** — returns a tuple `(local_ip, local_port)` representing the local address the OS bound the socket to after the `connect()` call above.

**`[0]`** — extracts just the IP address string from the tuple, discarding the port number.

**What this returns:** A string like `"192.168.1.23"` — the machine's actual LAN IP address, the one other devices on the network use to reach this machine.

---

```python
    except Exception:
        return "127.0.0.1"
```

**`except Exception`** — catches any error that occurred in the `try` block: socket creation failure, routing failure, permission error, etc.

**`return "127.0.0.1"`** — if IP detection fails, return the loopback address. The system still works; remote devices just cannot connect because `127.0.0.1` is not reachable from other machines. The logged URL will say `127.0.0.1:8000`.

---

```python
BACKEND_PORT: int = 8000
```

**`BACKEND_PORT`** — uppercase name signals a constant. All modules that need to know what port the backend runs on import this one value.

**`: int`** — type annotation. `BACKEND_PORT` should always hold an integer. This is checked by static analysis tools.

**`= 8000`** — port 8000 is a common choice for development servers. It is above port 1023 (no root permission required on Linux) and not used by any common system service.

**How it is used:** `uvicorn backend.main:app --port 8000` matches this. `routes.py` uses it in the streamer URL. `config.js` in the frontend uses it for the direct remote streamer link.

---

```python
CAMERA_INDEX_CANDIDATES: list[int] = [0, 1, 2, 3, 4]
```

**What is written?** A constant list of camera device indices to try when opening the local webcam.

**Why this order `[0, 1, 2, 3, 4]`?** Starting with 0 is the safe default. The previous `camera_capture.py` used `[1, 0, 2, 3, 4]`. Either order works — change it here without touching any other file.

**How it is used:** `backend/camera/local.py` reads `config.CAMERA_INDEX_CANDIDATES` in its `open()` method.

---

```python
MAX_FRAME_QUEUE: int = 5
```

**What is written?** Maximum number of frames that can wait in a `RemoteCamera`'s queue at any one time.

**Why 5?** At 20 FPS incoming from a remote device, 5 frames represent 250 ms of buffer. If the consumer (feed broadcaster) is slow, frames older than 250 ms are dropped instead of accumulating. This keeps the feed real-time.

**What if set to 1?** Almost every frame would be dropped, resulting in very low effective FPS in the React display.

**What if set to 100?** Old frames accumulate during any processing delay, causing the displayed video to lag behind reality by up to 5 seconds.

---

```python
REMOTE_READ_TIMEOUT: float = 0.05
```

**What is written?** 50 milliseconds — the maximum time `RemoteCamera.read()` waits for a frame before returning `(False, None)`.

**Why 50ms?** The feed broadcaster calls `active.read()` in a loop. If no frame arrives within 50ms, it returns `(False, None)` meaning "try again." This prevents the broadcaster from blocking for a long time when a remote device is slow.

**What if set to 5.0?** The broadcaster would freeze for up to 5 seconds waiting for each frame. During that time, the feed stops updating and all React clients show a frozen image.

---

```python
FEED_JPEG_QUALITY: int = 80
```

**What is written?** JPEG compression quality (0=worst/smallest, 100=best/largest) used when encoding frames to send to React.

**Why 80?** Provides a good balance: 80% quality JPEG is visually nearly indistinguishable from the original at typical video resolutions, but is roughly 4× smaller than a PNG. At 30 FPS and 1280×720, quality 80 produces approximately 30–80 KB per frame.

**What if set to 100?** Excellent quality but frames are 3–5× larger, potentially saturating the local WebSocket connection.

---

```python
LOCAL_IP: str = _get_local_ip()
```

**What is written?** Calls `_get_local_ip()` immediately when this module is imported and stores the result.

**Why at module level?** Every import of `config` gets the same IP value without calling the function again. IP detection is consistent across the entire backend session.

**How it is used:** `routes.py` substitutes `LOCAL_IP` into the streamer URL that is displayed to the user. `main.py` prints it in the startup banner.

---

## Step 3 — Camera Base Class

**Goal:** Define the contract that every camera type must fulfil. This is an interface — it specifies *what* methods must exist, not *how* they work.

**File:** `backend/camera/base.py` — **NEW**

### Complete Code

```python
from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np


class CameraSource(ABC):

    @abstractmethod
    def open(self) -> bool: ...

    @abstractmethod
    def read(self) -> tuple[bool, object]: ...

    @abstractmethod
    def release(self) -> None: ...

    @property
    @abstractmethod
    def device_id(self) -> str: ...

    @property
    @abstractmethod
    def label(self) -> str: ...

    @property
    @abstractmethod
    def width(self) -> int: ...

    @property
    @abstractmethod
    def height(self) -> int: ...

    @property
    @abstractmethod
    def fps(self) -> float: ...

    @property
    @abstractmethod
    def is_open(self) -> bool: ...

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} id={self.device_id!r} "
            f"label={self.label!r} open={self.is_open}>"
        )
```

### Understand the Code Line by Line

---

```python
from __future__ import annotations
```

**What is written?** A special import from Python's `__future__` module.

**What does it mean?** Enables "postponed evaluation of annotations." Without this, Python 3.9 and earlier would fail on type hints that reference types not yet defined, or on using newer generic syntax like `list[int]` instead of `List[int]`.

**Why include it?** Makes the type annotation `tuple[bool, object]` work on Python 3.9 and 3.10 without importing `from typing import Tuple`.

---

```python
from abc import ABC, abstractmethod
```

**`abc`** — Python's built-in "Abstract Base Classes" module.

**`ABC`** — a base class that, when inherited, gives a class the ability to declare abstract methods.

**`abstractmethod`** — a decorator that marks a method as abstract. Any class that inherits `CameraSource` must implement every `@abstractmethod` or Python raises `TypeError` when you try to instantiate it.

---

```python
import numpy as np
```

**What is written?** Imports NumPy with the conventional alias `np`.

**Why in `base.py`?** The return type of `read()` includes a NumPy `ndarray`. Importing numpy here makes the type available in the module. (In this stripped version the full type hint is in the docstring; numpy is available for subclasses that need it without importing again.)

---

```python
class CameraSource(ABC):
```

**`class CameraSource`** — defines a new class named `CameraSource`.

**`(ABC)`** — inherits from `ABC`. This activates the abstract method machinery. A class that inherits `ABC` cannot be instantiated if it has any unimplemented abstract methods.

**Why name it `CameraSource`?** It describes what it represents: a source of camera frames. Both `LocalCamera` and `RemoteCamera` are sources of camera frames.

---

```python
    @abstractmethod
    def open(self) -> bool: ...
```

**`@abstractmethod`** — decorator that marks `open` as abstract. Every subclass must provide its own `open()` implementation.

**`-> bool`** — return type annotation: `open()` must return `True` (success) or `False` (failure).

**`...`** — Python's ellipsis literal. Used as the body of abstract methods to indicate "no implementation here — subclasses must provide one."

**Why `open()` instead of opening in `__init__`?** Keeping initialisation separate from construction means you can create a `LocalCamera` object and decide later whether to open it. This is essential for the `DeviceRegistry`, which may hold references to cameras that are not yet active.

---

```python
    @abstractmethod
    def read(self) -> tuple[bool, object]: ...
```

**`tuple[bool, object]`** — returns a pair: a boolean success flag and a frame object.

**Why `object` and not `np.ndarray`?** The method is defined to return a three-state result:
- `(True, ndarray)` — valid frame
- `(False, None)` — non-fatal, queue empty, caller should retry
- `(False, non-None)` — fatal hardware failure, caller should remove device

Using `object` as the second type allows all three cases. The docstring in each subclass explains the specific contract.

---

```python
    @property
    @abstractmethod
    def device_id(self) -> str: ...
```

**`@property`** — decorator that turns `device_id` into a read-only property. Callers write `cam.device_id`, not `cam.device_id()`.

**`@abstractmethod`** — `@property` and `@abstractmethod` must both be present to create an abstract property. Order matters: `@property` goes on top.

**Why a property and not a method?** `cam.device_id` reads more naturally than `cam.get_device_id()`. Properties are the Pythonic way to expose read-only attributes.

---

```python
    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} id={self.device_id!r} "
            f"label={self.label!r} open={self.is_open}>"
        )
```

**`__repr__`** — Python's "representation" special method. Called when you print an object or use `repr(obj)`. This is the concrete method — subclasses inherit it for free.

**`type(self).__name__`** — returns the class name of the actual object. If a `LocalCamera` instance is printed, this shows `LocalCamera`, not `CameraSource`.

**`!r`** — applies `repr()` to the value, adding quotes around strings in the output.

**Example output:** `<LocalCamera id='local:0' label='Local Camera (index 0)' open=True>`

---

## Step 4 — Local Camera

**Goal:** Implement the local webcam as a `CameraSource`. Encapsulate the camera-opening logic from `camera_capture.py` into a proper class that can be instantiated, opened, and released independently.

**File:** `backend/camera/local.py` — **NEW**

### Complete Code

```python
from __future__ import annotations
import time
import cv2
import backend.config as config
from backend.camera.base import CameraSource


class LocalCamera(CameraSource):

    def __init__(self) -> None:
        self._cap:       cv2.VideoCapture | None = None
        self._width:     int   = 0
        self._height:    int   = 0
        self._fps:       float = 0.0
        self._is_open:   bool  = False
        self._cam_index: int   = -1

    def open(self) -> bool:
        if self._is_open:
            return True

        for idx in config.CAMERA_INDEX_CANDIDATES:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            time.sleep(0.5)

            if not cap.isOpened():
                cap.release()
                continue

            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if w == 0 or h == 0:
                cap.release()
                continue

            fps = cap.get(cv2.CAP_PROP_FPS)
            self._cap       = cap
            self._width     = w
            self._height    = h
            self._fps       = fps if fps > 0 else 0.0
            self._is_open   = True
            self._cam_index = idx
            print(f"[LocalCamera] Opened index {idx}: {w}x{h} @ {self._fps:.1f} FPS")
            return True

        print("[LocalCamera] No camera found at any index.")
        return False

    def read(self) -> tuple[bool, object]:
        if not self._is_open or self._cap is None:
            return False, None

        ok, frame = self._cap.read()
        if not ok:
            self._is_open = False
            print("[LocalCamera] Frame read failed — camera disconnected.")
            return False, b""

        return True, frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._is_open = False
        print(f"[LocalCamera] Released (index {self._cam_index}).")

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
```

### Understand the Code Line by Line

---

```python
import backend.config as config
```

**`import backend.config as config`** — imports the config module and gives it the short alias `config`.

**Why `as config`?** So we can write `config.CAMERA_INDEX_CANDIDATES` instead of `backend.config.CAMERA_INDEX_CANDIDATES`. Shorter and still clear where the value comes from.

---

```python
from backend.camera.base import CameraSource
```

**What is written?** Imports the `CameraSource` abstract base class from `base.py`.

**Why?** `LocalCamera` inherits from `CameraSource` (`class LocalCamera(CameraSource)`). Python needs `CameraSource` to be imported before the class definition.

---

```python
class LocalCamera(CameraSource):
```

**`(CameraSource)`** — declares that `LocalCamera` inherits from `CameraSource`. This means:
1. `LocalCamera` must implement every `@abstractmethod` defined in `CameraSource`.
2. `LocalCamera` instances can be stored anywhere that expects a `CameraSource`.
3. `isinstance(local_cam, CameraSource)` returns `True`.

---

```python
    def __init__(self) -> None:
        self._cap:       cv2.VideoCapture | None = None
        self._width:     int   = 0
        self._height:    int   = 0
        self._fps:       float = 0.0
        self._is_open:   bool  = False
        self._cam_index: int   = -1
```

**`__init__`** — Python's constructor, called when you write `LocalCamera()`.

**All attributes start with `_`** — the single underscore means "private to this class." External code should use the properties (`cam.width`) not the raw attributes (`cam._width`).

**`cv2.VideoCapture | None = None`** — the `|` syntax means "this variable can hold either a `cv2.VideoCapture` object or `None`." Starts as `None` because the camera has not been opened yet.

**`self._cam_index: int = -1`** — `-1` is a sentinel meaning "no camera opened yet." After a successful open, this holds the actual index (0, 1, 2…).

---

```python
    def open(self) -> bool:
        if self._is_open:
            return True
```

**`if self._is_open: return True`** — guard against double-opening. If `open()` is called twice, the second call returns `True` immediately without trying to open the camera again. Opening a camera that is already open would either fail or create a duplicate handle.

---

```python
        for idx in config.CAMERA_INDEX_CANDIDATES:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            time.sleep(0.5)
```

**Same logic as `camera_capture.py`** but with `0.5` seconds instead of `1`. The shorter wait is acceptable because `LocalCamera` is only instantiated once at startup (not on every import).

---

```python
            if w == 0 or h == 0:
                cap.release()
                continue
```

**What is written?** An extra validity check not present in the original `camera_capture.py`.

**Why?** Some drivers return `isOpened() = True` but `width = 0` and `height = 0` when the hardware is not ready. The 0.5-second sleep usually prevents this, but this check catches any remaining cases. A camera with zero-size resolution would cause division-by-zero errors later.

---

```python
    def read(self) -> tuple[bool, object]:
        if not self._is_open or self._cap is None:
            return False, None

        ok, frame = self._cap.read()
        if not ok:
            self._is_open = False
            return False, b""

        return True, frame
```

**`return False, None`** — the camera is not open. `None` as the second value signals "non-fatal, no frame available." The broadcaster sees `(False, None)` and retries.

**`return False, b""`** — `b""` is an empty bytes object — it is not `None`. This is the three-state protocol: `(False, non-None)` signals a **fatal** hardware failure. The broadcaster removes this camera from the registry.

**Why `b""` as the fatal sentinel?** It is a simple value that is definitely not `None` and not a valid frame array. Any non-None value would work; `b""` is chosen for clarity.

---

```python
    @property
    def device_id(self) -> str:
        return "local:0"
```

**`"local:0"`** — a hardcoded ID for the local camera. The prefix `"local:"` distinguishes it from remote cameras (whose IDs are random hex strings like `"a3f92b1c"`). The `DeviceRegistry` uses this string as a dictionary key.

**Why hardcoded?** There is only one local camera per machine. If the system ever supports multiple local cameras, this would become `f"local:{self._cam_index}"`.

---

## Step 5 — Remote Camera

**Goal:** Create a camera source that receives frames from a remote browser via WebSocket. The WebSocket receiver pushes frames in; the feed broadcaster reads them out.

**File:** `backend/camera/remote.py` — **NEW**

### Complete Code

```python
from __future__ import annotations
import queue
import numpy as np
import backend.config as config
from backend.camera.base import CameraSource


class RemoteCamera(CameraSource):

    def __init__(self, device_id: str, label: str) -> None:
        self._device_id = device_id
        self._label     = label
        self._queue: queue.Queue[np.ndarray] = queue.Queue(
            maxsize=config.MAX_FRAME_QUEUE
        )
        self._width:   int   = 0
        self._height:  int   = 0
        self._is_open: bool  = False

    def push_frame(self, frame: np.ndarray) -> None:
        if not self._is_open:
            self._is_open = True

        if self._width == 0:
            self._height, self._width = frame.shape[:2]

        if self._queue.full():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass

        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            pass

    def mark_disconnected(self) -> None:
        self._is_open = False

    def open(self) -> bool:
        return True

    def read(self) -> tuple[bool, object]:
        try:
            frame = self._queue.get(timeout=config.REMOTE_READ_TIMEOUT)
            return True, frame
        except queue.Empty:
            return False, None

    def release(self) -> None:
        self._is_open = False
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        print(f"[RemoteCamera] Released: {self._label}")

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label = value

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def fps(self) -> float:
        return 0.0

    @property
    def is_open(self) -> bool:
        return self._is_open
```

### Understand the Code Line by Line

---

```python
import queue
```

**`queue`** — Python's built-in thread-safe queue module. Provides `Queue`, `LifoQueue`, `PriorityQueue`.

**Why thread-safe?** `push_frame()` is called from one asyncio coroutine (the WebSocket handler). `read()` is called from another coroutine (the broadcaster). Even though both run in the same asyncio event loop, `queue.Queue` is used because it handles concurrent access correctly and is familiar to all Python developers.

---

```python
    def __init__(self, device_id: str, label: str) -> None:
```

**`device_id: str`** — a unique identifier passed in by `ws_receiver.py`. It is a random 8-character hex string like `"a3f92b1c"`.

**`label: str`** — human-readable name shown in the UI, e.g., `"iPhone (192.168.1.5)"`.

**Why are these parameters?** `RemoteCamera` does not know its own ID — that is assigned by the WebSocket receiver when the connection arrives. Passing them in keeps the class reusable and testable.

---

```python
        self._queue: queue.Queue[np.ndarray] = queue.Queue(
            maxsize=config.MAX_FRAME_QUEUE
        )
```

**`queue.Queue[np.ndarray]`** — the type annotation says "this queue holds NumPy arrays."

**`maxsize=config.MAX_FRAME_QUEUE`** — limits the queue to 5 frames. When full, `put_nowait()` raises `queue.Full`.

**Why limit the queue?** Without a limit, if the broadcaster reads slowly, the queue grows without bound. After 10 seconds, the displayed video could be 10 seconds behind real time. A queue of 5 frames at 20 FPS = 250ms maximum lag.

---

```python
    def push_frame(self, frame: np.ndarray) -> None:
        if not self._is_open:
            self._is_open = True

        if self._width == 0:
            self._height, self._width = frame.shape[:2]
```

**`if not self._is_open: self._is_open = True`** — the camera becomes "open" as soon as the first frame arrives. Before the first frame, the camera is in a "connected but no data yet" state.

**`frame.shape[:2]`** — a NumPy ndarray has a `.shape` attribute like `(720, 1280, 3)`. `[:2]` takes the first two values: `(720, 1280)`. Assignment `self._height, self._width = (720, 1280)` unpacks these.

**Why not set width/height in `__init__`?** The frame dimensions are not known until the first frame arrives. The browser determines resolution — the backend discovers it from the first decoded JPEG.

---

```python
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
```

**`self._queue.full()`** — returns `True` if the queue has reached `maxsize`.

**`self._queue.get_nowait()`** — removes and discards the oldest frame from the queue without waiting.

**`except queue.Empty: pass`** — in theory, if `full()` was `True`, `get_nowait()` should succeed. But in rare race conditions on multi-threaded systems, another consumer could have removed the item first. The `except` makes this safe.

**Why discard the oldest?** The newest frame is the most current view of the remote camera. When backpressure builds, dropping old frames keeps the display as real-time as possible.

---

```python
    def mark_disconnected(self) -> None:
        self._is_open = False
```

**What is written?** A method called by `ws_receiver.py` when the browser WebSocket closes.

**Why a separate method and not just `release()`?** `mark_disconnected()` only sets the flag — it does not drain the queue. This allows the broadcaster to still deliver any remaining queued frames before `release()` is called by the registry.

---

```python
    def read(self) -> tuple[bool, object]:
        try:
            frame = self._queue.get(timeout=config.REMOTE_READ_TIMEOUT)
            return True, frame
        except queue.Empty:
            return False, None
```

**`self._queue.get(timeout=0.05)`** — blocks the calling thread for up to 50ms waiting for a frame. If a frame arrives in that time, it is returned. If not, `queue.Empty` is raised.

**`return True, frame`** — success: a valid NumPy BGR frame.

**`return False, None`** — no frame arrived within 50ms. `None` signals "non-fatal, try again." The broadcaster loops back immediately and calls `read()` again.

**Critical difference from `LocalCamera`:** `LocalCamera.read()` returns `(False, b"")` on fatal failure. `RemoteCamera.read()` never returns a fatal signal — when the device disconnects, `ws_receiver.py` calls `registry.remove()` which calls `release()`. The camera object is simply deleted from the registry.

---

```python
    @label.setter
    def label(self, value: str) -> None:
        self._label = value
```

**`@label.setter`** — creates a writable property. After the `@property` definition, this allows `cam.label = "new name"` in addition to reading `cam.label`.

**Why is a setter needed?** When the browser sends its device name as the first text message (e.g., `{"name": "iPhone Rear"}`), `ws_receiver.py` updates the label: `cam.label = f"{name} ({peer_ip})"`. Without a setter, this would raise `AttributeError: can't set attribute`.

---

## Step 6 — Device Registry

**Goal:** Create a thread-safe dictionary that maps device IDs to `CameraSource` objects. This is the single location in the backend that knows which cameras exist and which one is active.

**File:** `backend/devices/registry.py` — **NEW**

### Complete Code

```python
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
            self._devices[cam.device_id] = cam
            if self._active_id is None:
                self._active_id = cam.device_id

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

    def set_active(self, device_id: str) -> bool:
        with self._lock:
            if device_id not in self._devices:
                return False
            self._active_id = device_id
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
            if self._active_id is None:
                return None
            return self._devices.get(self._active_id)

    def get(self, device_id: str) -> Optional[CameraSource]:
        with self._lock:
            return self._devices.get(device_id)

    def list_devices(self) -> list[tuple[str, CameraSource, bool]]:
        with self._lock:
            return [
                (did, cam, did == self._active_id)
                for did, cam in self._devices.items()
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._devices)


registry = DeviceRegistry()
```

### Understand the Code Line by Line

---

```python
import threading
```

**`threading`** — Python's built-in module for thread management. We use only `threading.Lock` from it.

---

```python
from typing import Optional
```

**`Optional[str]`** — type alias for `str | None`. Means "a string or None." Used for `_active_id` which starts as `None` and becomes a string when the first camera is added.

---

```python
        self._lock = threading.Lock()
```

**`threading.Lock()`** — creates a mutual exclusion lock. Only one thread/coroutine can hold the lock at a time.

**Why needed?** The WebSocket receiver (adds/removes cameras) and the feed broadcaster (reads `get_active()`) both access `_devices` concurrently. Without a lock, one coroutine could modify `_devices` while another is iterating it, causing `RuntimeError: dictionary changed size during iteration`.

---

```python
        self._devices: dict[str, CameraSource] = {}
```

**`dict[str, CameraSource]`** — a dictionary mapping device ID strings to `CameraSource` objects.

**Python 3.7+ dict is insertion-ordered.** Devices appear in the order they were added. The device list in the React UI follows this order.

---

```python
    def add(self, cam: CameraSource) -> None:
        with self._lock:
            self._devices[cam.device_id] = cam
            if self._active_id is None:
                self._active_id = cam.device_id
```

**`with self._lock:`** — acquires the lock when entering the block, releases it when exiting (even if an exception occurs). All code inside this block is protected from concurrent modification.

**`self._devices[cam.device_id] = cam`** — stores the camera using its `device_id` as the key.

**`if self._active_id is None: self._active_id = cam.device_id`** — if no camera was active before (first device added), make this camera active immediately. This means the first camera added (local camera) is automatically the default view.

---

```python
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
```

**`self._devices.pop(device_id, None)`** — removes and returns the camera for `device_id`. The second argument `None` means "return `None` if key does not exist" instead of raising `KeyError`.

**`try: cam.release() except Exception: pass`** — calls `release()` to free hardware resources. The `try/except` prevents a buggy camera's `release()` method from crashing the registry.

**`next(iter(self._devices), None)`** — if the removed camera was active, switch to the first remaining camera. `iter(self._devices)` creates an iterator over dictionary keys (in insertion order). `next(..., None)` returns the first key, or `None` if the dictionary is empty.

---

```python
    def list_devices(self) -> list[tuple[str, CameraSource, bool]]:
        with self._lock:
            return [
                (did, cam, did == self._active_id)
                for did, cam in self._devices.items()
            ]
```

**`self._devices.items()`** — returns pairs of `(device_id, camera_object)`.

**`did == self._active_id`** — computes a boolean for each device indicating whether it is the currently active camera.

**Why return a list and not an iterator?** The list is built while the lock is held, then returned. The caller iterates the returned list without the lock. If we returned an iterator, the caller would iterate after releasing the lock, potentially iterating a dictionary that changes size — a runtime error.

---

```python
registry = DeviceRegistry()
```

**What is written?** Creates a single `DeviceRegistry` instance at module level.

**Why a singleton?** Every module that needs the registry (`ws_receiver.py`, `routes.py`, `feed.py`, `main.py`) imports this one object: `from backend.devices.registry import registry`. They all reference the same instance, so they all see the same device list.

**What if each module created its own `DeviceRegistry()`?** Each module would have a separate empty registry. A device added by `ws_receiver` would not appear in `routes.py`'s list.

---

## Step 7 — WebSocket Receiver

**Goal:** Accept WebSocket connections from remote browsers. For each connection, create a `RemoteCamera`, register it, decode incoming JPEG frames, and push them to the camera's queue. Clean up when the browser disconnects.

**File:** `backend/transport/ws_receiver.py` — **NEW**

### Complete Code

```python
from __future__ import annotations
import json
import uuid
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.camera.remote import RemoteCamera
from backend.devices.registry import registry

router = APIRouter()
_connections: dict[str, WebSocket] = {}


@router.websocket("/ws/device")
async def device_stream(websocket: WebSocket) -> None:
    await websocket.accept()

    device_id = uuid.uuid4().hex[:8]
    peer_ip   = websocket.client.host if websocket.client else "unknown"
    label     = f"Remote ({peer_ip})"

    cam = RemoteCamera(device_id, label)
    cam.open()
    registry.add(cam)
    _connections[device_id] = websocket

    print(f"[WsReceiver] Connected: {label} [id={device_id}]")

    try:
        while True:
            data = await websocket.receive()

            if data.get("text"):
                try:
                    info = json.loads(data["text"])
                    name = info.get("name", "").strip()
                    if name:
                        cam.label = f"{name} ({peer_ip})"
                        print(f"[WsReceiver] Named: {cam.label}")
                except (json.JSONDecodeError, AttributeError):
                    pass

            elif data.get("bytes"):
                buf   = np.frombuffer(data["bytes"], dtype=np.uint8)
                frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                if frame is not None:
                    cam.push_frame(frame)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WsReceiver] Error for {label}: {type(e).__name__}: {e}")
    finally:
        cam.mark_disconnected()
        registry.remove(device_id)
        _connections.pop(device_id, None)
        print(f"[WsReceiver] Disconnected: {label} [id={device_id}]")


async def close_device(device_id: str) -> None:
    ws = _connections.get(device_id)
    if ws is not None:
        try:
            await ws.close()
        except Exception:
            pass
```

### Understand the Code Line by Line

---

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
```

**`APIRouter`** — FastAPI's way to group related routes. The router is imported into `main.py` with `app.include_router(ws_receiver.router)`.

**`WebSocket`** — FastAPI's WebSocket class. Used as a type annotation for the parameter that receives the connection.

**`WebSocketDisconnect`** — exception raised by FastAPI/Starlette when the remote side closes the connection (browser tab closed, network lost, `ws.close()` called in JS).

---

```python
router = APIRouter()
```

**What is written?** Creates a router object that collects route definitions.

**Why a router instead of registering directly on `app`?** Routers keep related routes together in one file. `main.py` registers the router with `app.include_router(ws_receiver.router)` — a single line that brings all this file's routes into the application.

---

```python
_connections: dict[str, WebSocket] = {}
```

**`_connections`** — a module-level dictionary mapping `device_id` to the live `WebSocket` object.

**Why store these?** `close_device(device_id)` needs to close the WebSocket from outside this coroutine — specifically when the React user clicks "Disconnect." Without this dict, there is no way to find the WebSocket object for a given device.

**Thread safety note:** This dict is accessed only from the asyncio event loop (the WebSocket handler coroutines and `close_device`). Since asyncio is single-threaded (cooperative multitasking), no concurrent modification occurs and no lock is needed.

---

```python
@router.websocket("/ws/device")
async def device_stream(websocket: WebSocket) -> None:
```

**`@router.websocket("/ws/device")`** — registers `device_stream` as the handler for WebSocket connections to the URL `/ws/device`. FastAPI calls this coroutine each time a new browser connects.

**`async def`** — defines a coroutine. FastAPI runs it inside its asyncio event loop. Multiple device connections are handled concurrently — FastAPI creates a separate coroutine instance for each connection.

**`websocket: WebSocket`** — FastAPI injects the WebSocket connection object for this specific connection.

---

```python
    await websocket.accept()
```

**`await`** — suspends this coroutine and lets the event loop do other work while waiting for the operation to complete.

**`websocket.accept()`** — completes the WebSocket handshake. Before calling `accept()`, the connection is in the HTTP upgrade state. After `accept()`, binary and text messages can be sent and received. If `accept()` is never called, the browser times out.

---

```python
    device_id = uuid.uuid4().hex[:8]
```

**`uuid.uuid4()`** — generates a random 128-bit UUID (version 4 = random).

**`.hex`** — converts the UUID to a 32-character hexadecimal string without dashes, e.g., `"a3f92b1cd8e74f0a..."`.

**`[:8]`** — takes only the first 8 characters, e.g., `"a3f92b1c"`. This is short enough to be human-readable in logs while being statistically unique (16^8 = ~4 billion possible IDs).

---

```python
    peer_ip = websocket.client.host if websocket.client else "unknown"
```

**`websocket.client`** — a `(host, port)` tuple identifying the remote end of the connection, or `None` if the information is not available (behind certain proxies).

**`websocket.client.host`** — the remote IP address string, e.g., `"192.168.1.5"`.

**`if websocket.client else "unknown"`** — defensive check. If `websocket.client` is `None`, use the string `"unknown"` rather than crashing with `AttributeError`.

---

```python
            data = await websocket.receive()
```

**`websocket.receive()`** — waits for the next message from the browser. Returns a dictionary with these keys:
- `"type"` — always `"websocket.receive"`
- `"bytes"` — binary data if the browser sent binary; `None` otherwise
- `"text"` — text string if the browser sent text; `None` otherwise

**Why `.receive()` instead of `.receive_bytes()` or `.receive_text()`?** The browser sends two types of messages: a JSON text message first (device name), then binary JPEG frames. `.receive()` handles both. `.receive_bytes()` would fail on the text message.

---

```python
                buf   = np.frombuffer(data["bytes"], dtype=np.uint8)
                frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
```

**`np.frombuffer(data["bytes"], dtype=np.uint8)`** — interprets the raw JPEG binary data as a 1-D NumPy array of unsigned 8-bit integers. This does not decode the JPEG — it just wraps the bytes in an array structure that OpenCV can process.

**`cv2.imdecode(buf, cv2.IMREAD_COLOR)`** — decodes the JPEG-compressed data back into an uncompressed BGR image array of shape `(height, width, 3)`.

**`cv2.IMREAD_COLOR`** — flag telling OpenCV to decode into a 3-channel BGR image (not greyscale, not BGRA). This is the format that `cv2.imencode` expects when re-encoding for the React feed.

**`if frame is not None`** — `cv2.imdecode` returns `None` if the data is corrupt or not a valid JPEG. Silently skipping corrupt frames is better than crashing.

---

```python
    except WebSocketDisconnect:
        pass
```

**`except WebSocketDisconnect: pass`** — when the browser closes the connection, FastAPI raises `WebSocketDisconnect`. We catch it and do nothing (the `finally` block handles cleanup).

**Why `pass` and not some error message?** A disconnect is a normal event — the user closed their browser tab. It is not an error.

---

```python
    finally:
        cam.mark_disconnected()
        registry.remove(device_id)
        _connections.pop(device_id, None)
```

**`finally`** — runs regardless of how the loop exited: normal disconnect, unexpected exception, or `close_device()` calling `ws.close()`.

**Order matters:** `mark_disconnected()` is called before `registry.remove()`. This sets `cam.is_open = False` first, so if the broadcaster reads `get_active()` between these two calls, it sees an inactive camera and waits rather than trying to read from a dead queue.

---

```python
async def close_device(device_id: str) -> None:
    ws = _connections.get(device_id)
    if ws is not None:
        try:
            await ws.close()
        except Exception:
            pass
```

**`async def`** — this is a coroutine because `ws.close()` is async (it sends a WebSocket close frame to the browser and waits for acknowledgement).

**`_connections.get(device_id)`** — looks up the WebSocket. Returns `None` if not found (device already disconnected, or it was the local camera which has no WebSocket).

**`await ws.close()`** — sends a WebSocket close frame. The browser receives it and its `ws.onclose` event fires. On the server side, this causes `device_stream`'s `receive()` call to raise `WebSocketDisconnect`, which triggers the `finally` cleanup block.

---

## Step 8 — Browser Streamer Page

**Goal:** Create the HTML page that runs in remote device browsers. It accesses the device camera, captures frames, compresses them as JPEG, and sends them to the backend WebSocket.

**File:** `backend/transport/static/streamer.html` — **NEW**

### Complete Code

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
  <title>HTS — Remote Camera</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0f0f1a; --surface: #1a1a2e; --accent: #00c896;
      --text: #e0e0e0; --text-dim: #888; --danger: #e05050; --border: #2a2a45;
    }
    body {
      background: var(--bg); color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      min-height: 100dvh; display: flex; flex-direction: column;
      align-items: center; padding: 20px 16px 32px; gap: 16px;
    }
    header { width: 100%; max-width: 540px; }
    header h1 { font-size: 1.1rem; color: var(--accent); font-weight: 700; }
    header p  { font-size: 0.75rem; color: var(--text-dim); }
    .card {
      width: 100%; max-width: 540px; background: var(--surface);
      border: 1px solid var(--border); border-radius: 14px; padding: 16px;
    }
    #preview-wrap {
      position: relative; width: 100%; aspect-ratio: 16/9;
      background: #0a0a14; border-radius: 10px; overflow: hidden;
    }
    #video { width: 100%; height: 100%; object-fit: cover; display: block; }
    #placeholder {
      position: absolute; inset: 0; display: flex;
      align-items: center; justify-content: center;
      color: var(--text-dim); font-size: 0.85rem;
    }
    #placeholder.hidden { display: none; }
    #live-badge {
      position: absolute; top: 10px; left: 10px; background: var(--danger);
      color: #fff; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em;
      padding: 3px 8px; border-radius: 4px; display: none;
    }
    #live-badge.visible { display: block; }
    #status-bar { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; padding: 10px 0 4px; }
    #status-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--text-dim); flex-shrink: 0; }
    #status-dot.streaming { background: var(--accent); animation: pulse 1.2s infinite; }
    #status-dot.error { background: var(--danger); }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
    .field-label { font-size: 0.72rem; color: var(--text-dim); margin: 14px 0 5px; }
    #device-name {
      width: 100%; background: #0f0f1a; border: 1px solid var(--border);
      border-radius: 8px; color: var(--text); font-size: 0.88rem; padding: 10px 12px; outline: none;
    }
    #device-name:focus { border-color: var(--accent); }
    .controls { display: flex; gap: 10px; padding-top: 12px; flex-wrap: wrap; }
    button { flex: 1; min-width: 100px; padding: 13px 16px; border: none; border-radius: 10px; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
    button:disabled { opacity: 0.4; cursor: default; }
    #btn-start { background: var(--accent); color: #000; }
    #btn-stop  { background: var(--danger); color: #fff; display: none; }
    #btn-flip  { background: var(--border); color: var(--text); flex: 0 0 auto; }
    #stats { font-size: 0.72rem; color: var(--text-dim); padding-top: 10px; }
    .info { font-size: 0.72rem; color: var(--text-dim); text-align: center; }
  </style>
</head>
<body>
  <header>
    <h1>HTS Remote Camera</h1>
    <p>Human Tracking System — Device Streamer</p>
  </header>
  <div class="card">
    <div id="preview-wrap">
      <video id="video" autoplay playsinline muted></video>
      <div id="placeholder">📷 Camera preview will appear here</div>
      <div id="live-badge">● LIVE</div>
    </div>
    <div id="status-bar">
      <div id="status-dot"></div>
      <span id="status-text">Enter a name and tap Start Streaming.</span>
    </div>
    <p class="field-label">Device name (shown on laptop)</p>
    <input id="device-name" type="text" maxlength="40" placeholder="e.g. iPhone Rear, Lab Cam 2" />
    <div class="controls">
      <button id="btn-start" onclick="startStreaming()">▶ Start Streaming</button>
      <button id="btn-stop"  onclick="stopStreaming()">■ Stop</button>
      <button id="btn-flip"  onclick="flipCamera()">🔄 Flip</button>
    </div>
    <div id="stats"></div>
  </div>
  <p class="info">No app required. Same Wi-Fi network required.</p>

<script>
  "use strict";

  const WS_URL       = "ws://{{WS_HOST}}:{{WS_PORT}}/ws/device";
  const JPEG_QUALITY = 0.80;
  const TARGET_FPS   = 20;

  let ws = null, stream = null, sending = false;
  let lastSent = 0, framesSent = 0, bytesSent = 0;
  let facingMode = "environment";

  const video       = document.getElementById("video");
  const canvas      = document.createElement("canvas");
  const ctx         = canvas.getContext("2d");
  const statusDot   = document.getElementById("status-dot");
  const statusText  = document.getElementById("status-text");
  const liveBadge   = document.getElementById("live-badge");
  const placeholder = document.getElementById("placeholder");
  const btnStart    = document.getElementById("btn-start");
  const btnStop     = document.getElementById("btn-stop");
  const statsEl     = document.getElementById("stats");

  function setStatus(text, state) {
    statusText.textContent = text;
    statusDot.className = state || "";
  }

  async function openCamera() {
    if (stream) stream.getTracks().forEach(t => t.stop());
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: facingMode }, width: {ideal:1280}, height: {ideal:720} },
        audio: false,
      });
    } catch {
      setStatus("Camera denied. Check browser permissions.", "error");
      return null;
    }
    video.srcObject = stream;
    placeholder.classList.add("hidden");
    await video.play().catch(() => {});
    return stream;
  }

  async function startStreaming() {
    btnStart.disabled = true;
    setStatus("Opening camera…", "");
    if (!await openCamera()) { btnStart.disabled = false; return; }
    setStatus("Connecting to backend…", "");
    ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      const name = document.getElementById("device-name").value.trim()
                   || "Device " + Math.floor(Math.random() * 9000 + 1000);
      ws.send(JSON.stringify({ type: "init", name }));
      setStatus("Streaming to laptop", "streaming");
      liveBadge.classList.add("visible");
      btnStart.style.display = "none";
      btnStop.style.display  = "";
      sending = true;
      requestAnimationFrame(sendFrame);
    };

    ws.onclose = () => {
      setStatus("Disconnected. Tap Start to reconnect.", "");
      liveBadge.classList.remove("visible");
      sending = false;
      btnStart.style.display = "";
      btnStop.style.display  = "none";
      btnStart.disabled = false;
    };

    ws.onerror = () => setStatus("Connection error. Is the laptop running?", "error");
  }

  function stopStreaming() {
    sending = false;
    if (ws)     { ws.close(); ws = null; }
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    video.srcObject = null;
    placeholder.classList.remove("hidden");
    liveBadge.classList.remove("visible");
    btnStart.style.display = "";
    btnStop.style.display  = "none";
    btnStart.disabled = false;
    setStatus("Stopped.", "");
  }

  async function flipCamera() {
    facingMode = facingMode === "environment" ? "user" : "environment";
    if (stream) await openCamera();
  }

  function sendFrame(ts) {
    if (!sending) return;
    if (ts - lastSent < 1000 / TARGET_FPS) { requestAnimationFrame(sendFrame); return; }
    lastSent = ts;
    const w = video.videoWidth, h = video.videoHeight;
    if (!w || !h) { requestAnimationFrame(sendFrame); return; }
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    ctx.drawImage(video, 0, 0, w, h);
    canvas.toBlob(blob => {
      if (!blob || !ws || ws.readyState !== WebSocket.OPEN) return;
      blob.arrayBuffer().then(buf => {
        ws.send(buf);
        framesSent++;
        bytesSent += buf.byteLength;
        statsEl.textContent = `${framesSent} frames · ${(bytesSent/1024).toFixed(0)} KB`;
      });
    }, "image/jpeg", JPEG_QUALITY);
    requestAnimationFrame(sendFrame);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) sending = false;
    else if (ws?.readyState === WebSocket.OPEN) { sending = true; requestAnimationFrame(sendFrame); }
  });
</script>
</body>
</html>
```

### Understand the Key JavaScript Lines

---

```javascript
const WS_URL = "ws://{{WS_HOST}}:{{WS_PORT}}/ws/device";
```

**`{{WS_HOST}}` and `{{WS_PORT}}`** — placeholder strings that are replaced by the Python backend in `routes.py` before the HTML is sent to the browser: `html.replace("{{WS_HOST}}", config.LOCAL_IP)`.

**Result:** When a browser receives this page, the URL is already resolved to something like `"ws://192.168.1.23:8000/ws/device"`. The browser connects directly to the backend.

**Why not a relative URL like `/ws/device`?** The remote device is on a different machine. Relative URLs resolve to the device's own address, not the laptop's. The full IP is required.

---

```javascript
const JPEG_QUALITY = 0.80;
const TARGET_FPS   = 20;
```

**`JPEG_QUALITY`** — passed to `canvas.toBlob()`. `0.80` = 80% JPEG quality.

**`TARGET_FPS`** — the maximum frames per second this browser will send. 20 FPS produces a smooth video stream while keeping bandwidth under control.

---

```javascript
let facingMode = "environment";
```

**`"environment"`** — W3C MediaDevices API facing mode. On a phone, `"environment"` selects the rear camera. `"user"` selects the front (selfie) camera. On a laptop webcam, both values select the only available camera.

---

```javascript
const canvas = document.createElement("canvas");
```

**`document.createElement("canvas")`** — creates an HTML canvas element in memory without adding it to the visible page.

**Why an off-screen canvas?** The browser's `<video>` element plays the camera stream. To capture a single frame as a JPEG, we must draw the video onto a canvas and then call `canvas.toBlob()`. The canvas never needs to be visible.

---

```javascript
stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: { ideal: facingMode }, width: {ideal:1280}, height: {ideal:720} },
    audio: false,
});
```

**`navigator.mediaDevices.getUserMedia()`** — W3C standard browser API. Opens the device camera and microphone. Returns a `Promise` that resolves to a `MediaStream`.

**`{ ideal: facingMode }`** — `ideal` means "prefer this, but do not fail if unavailable." If only a front camera exists and we ask for `"environment"`, the browser gives us the front camera anyway.

**`width: {ideal:1280}, height: {ideal:720}`** — requests 720p resolution. `ideal` means the browser will try to get this resolution but falls back to whatever the camera supports.

**`audio: false`** — we only need video. Omitting this or setting `true` would request microphone access too, which is unnecessary and would show a microphone permission prompt.

---

```javascript
ws.send(JSON.stringify({ type: "init", name }));
```

**`JSON.stringify({...})`** — converts the JavaScript object to a JSON string: `'{"type":"init","name":"iPhone Rear"}'`.

**`ws.send(string)`** — sends a text message over WebSocket. The backend's `data.get("text")` check in `ws_receiver.py` receives this.

**`{ type: "init", name }`** — shorthand for `{ type: "init", name: name }`. The `name` variable value is the device label the user typed.

---

```javascript
function sendFrame(ts) {
    if (!sending) return;
    if (ts - lastSent < 1000 / TARGET_FPS) { requestAnimationFrame(sendFrame); return; }
```

**`requestAnimationFrame(sendFrame)`** — the browser calls `sendFrame` before the next screen repaint, passing the current timestamp in milliseconds as `ts`. This is typically 60 times per second (60 FPS monitor).

**`1000 / TARGET_FPS`** — `1000 / 20 = 50` milliseconds per frame. If fewer than 50ms have passed since the last frame was sent, we skip this frame and reschedule.

**Why FPS throttle?** The camera and screen run at 60 FPS but the backend only needs 20 FPS for a smooth video stream. Sending 60 FPS would triple the bandwidth and CPU usage unnecessarily.

---

```javascript
    canvas.toBlob(blob => {
        blob.arrayBuffer().then(buf => {
            ws.send(buf);
        });
    }, "image/jpeg", JPEG_QUALITY);
```

**`canvas.toBlob(callback, type, quality)`** — asynchronously encodes the canvas content as an image and calls `callback` with the resulting `Blob` object.

**`"image/jpeg"`** — encode as JPEG (smaller than PNG, acceptable quality loss for video).

**`blob.arrayBuffer()`** — converts the `Blob` to an `ArrayBuffer` (raw binary data in memory).

**`ws.send(buf)`** — sends the `ArrayBuffer` as a binary WebSocket message. The backend receives it in `data["bytes"]`.

**Why `arrayBuffer()` and not send the `Blob` directly?** Some older browsers and WebSocket implementations do not support sending `Blob` objects directly. `ArrayBuffer` has universal support.

---

```javascript
document.addEventListener("visibilitychange", () => {
    if (document.hidden) sending = false;
    else if (ws?.readyState === WebSocket.OPEN) { sending = true; requestAnimationFrame(sendFrame); }
});
```

**`visibilitychange`** — fires when the browser tab becomes visible or hidden (user switches tabs or minimises the browser).

**`document.hidden`** — `true` when the tab is not visible.

**Why pause when hidden?** Mobile browsers throttle or stop JavaScript when a tab is backgrounded. Trying to read camera frames and send WebSocket messages in a hidden tab wastes battery and may fail silently.

---

## Step 9 — REST API Routes

**Goal:** Create the HTTP endpoints that React calls to manage devices.

**File:** `backend/api/routes.py` — **NEW**

### Complete Code

```python
from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import backend.config as config
from backend.devices.registry import registry
from backend.transport import ws_receiver

router = APIRouter()

_STREAMER_PATH = (
    Path(__file__).parent.parent / "transport" / "static" / "streamer.html"
)


@router.get("/devices")
def get_devices() -> list[dict]:
    return [
        {
            "id":        device_id,
            "label":     cam.label,
            "width":     cam.width,
            "height":    cam.height,
            "is_open":   cam.is_open,
            "is_active": is_active,
        }
        for device_id, cam, is_active in registry.list_devices()
    ]


@router.post("/devices/{device_id}/active")
def set_active_device(device_id: str) -> dict:
    if not registry.set_active(device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "ok", "active": device_id}


@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(device_id: str) -> dict:
    await ws_receiver.close_device(device_id)
    registry.remove(device_id)
    return {"status": "ok"}


@router.get("/streamer", response_class=HTMLResponse)
def serve_streamer() -> HTMLResponse:
    try:
        html = _STREAMER_PATH.read_text(encoding="utf-8")
    except OSError:
        raise HTTPException(status_code=500, detail="streamer.html not found")
    html = html.replace("{{WS_HOST}}", config.LOCAL_IP)
    html = html.replace("{{WS_PORT}}", str(config.BACKEND_PORT))
    return HTMLResponse(content=html)
```

### Understand the Code Line by Line

---

```python
from pathlib import Path
```

**`pathlib.Path`** — Python's object-oriented file path library. `Path` objects handle path joining, file reading, and OS path differences without string concatenation.

---

```python
from fastapi import APIRouter, HTTPException
```

**`HTTPException`** — FastAPI exception class. When raised, FastAPI converts it to an HTTP response with the specified status code and detail message. For example, `raise HTTPException(status_code=404)` sends `{"detail": "Not Found"}` to the client.

---

```python
from fastapi.responses import HTMLResponse
```

**`HTMLResponse`** — a FastAPI response type that sets the `Content-Type` header to `text/html`. Without this, FastAPI would set `Content-Type: application/json`, and the browser would display the raw HTML source rather than rendering it.

---

```python
_STREAMER_PATH = (
    Path(__file__).parent.parent / "transport" / "static" / "streamer.html"
)
```

**`Path(__file__)`** — `__file__` is Python's special variable containing the absolute path of the current file (`backend/api/routes.py`).

**`.parent`** — goes up one directory level: from `backend/api/routes.py` to `backend/api/`.

**`.parent.parent`** — goes up one more level: to `backend/`.

**`/ "transport" / "static" / "streamer.html"`** — the `/` operator on `Path` objects joins path components. This builds `backend/transport/static/streamer.html`.

**Why compute this at module level?** The path is computed once when the module loads, not on every request. This is more efficient and easier to debug.

---

```python
@router.get("/devices")
def get_devices() -> list[dict]:
    return [
        {
            "id":        device_id,
            "label":     cam.label,
            ...
        }
        for device_id, cam, is_active in registry.list_devices()
    ]
```

**`@router.get("/devices")`** — registers this function as the handler for `GET /api/devices` (the `/api` prefix is added when the router is included in `main.py`).

**List comprehension** — builds a list of dictionaries, one per device. `registry.list_devices()` returns a list of `(device_id, cam, is_active)` tuples. For each tuple, a dictionary is built.

**FastAPI auto-serialises the return value** — because this function returns a Python list of dicts, FastAPI automatically serialises it to JSON and sets `Content-Type: application/json`. No explicit `jsonify()` call needed.

---

```python
@router.post("/devices/{device_id}/active")
def set_active_device(device_id: str) -> dict:
    if not registry.set_active(device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "ok", "active": device_id}
```

**`{device_id}`** — a URL path parameter. FastAPI extracts the value from the URL and passes it as the `device_id` argument. For `POST /api/devices/a3f92b1c/active`, `device_id` = `"a3f92b1c"`.

**`raise HTTPException(status_code=404, ...)`** — if `set_active` returns `False` (device not found), respond with HTTP 404. React receives a non-OK response and can show an error.

---

```python
@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(device_id: str) -> dict:
    await ws_receiver.close_device(device_id)
    registry.remove(device_id)
    return {"status": "ok"}
```

**`async def`** — this endpoint is async because `ws_receiver.close_device()` is a coroutine (`async def`). You cannot `await` a coroutine from a regular `def` function.

**`await ws_receiver.close_device(device_id)`** — closes the remote device's WebSocket, which triggers the `finally` block in `ws_receiver.device_stream`, which calls `registry.remove()` itself. The explicit `registry.remove(device_id)` below handles the case where the device was already disconnected (local camera) and `close_device` did nothing.

---

```python
@router.get("/streamer", response_class=HTMLResponse)
def serve_streamer() -> HTMLResponse:
    ...
    html = html.replace("{{WS_HOST}}", config.LOCAL_IP)
    html = html.replace("{{WS_PORT}}", str(config.BACKEND_PORT))
    return HTMLResponse(content=html)
```

**`str(config.BACKEND_PORT)`** — `BACKEND_PORT` is an `int`. `replace()` requires a `str`, so we convert it.

**Two `replace()` calls** — Python strings are immutable. Each `replace()` creates a new string with the placeholder swapped out. The result of the first call is used as the input to the second call.

**Why serve HTML through Python instead of as a static file?** Static files cannot have their content modified at request time. Serving through Python lets us inject the correct IP and port from `config.py` before sending.

---

## Step 10 — Video Feed WebSocket

**Goal:** Create the WebSocket endpoint that React connects to. A background broadcaster reads from the active camera continuously and pushes encoded frames to every connected React client.

**File:** `backend/api/feed.py` — **NEW**

### Complete Code

```python
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
                await asyncio.sleep(0.01)
                continue
            else:
                print(f"[Feed] Fatal camera failure: {active.label}")
                registry.remove(active.device_id)
                continue

        encode_params = [cv2.IMWRITE_JPEG_QUALITY, config.FEED_JPEG_QUALITY]
        _, buf = cv2.imencode(".jpg", frame, encode_params)
        b64 = base64.b64encode(buf.tobytes()).decode("ascii")

        curr      = time.time()
        fps       = round(1.0 / (curr - prev_time), 1) if curr != prev_time else 0.0
        prev_time = curr

        msg = json.dumps({
            "type":  "frame",
            "frame": b64,
            "label": active.label,
            "fps":   fps,
        })

        await _broadcast(msg)


async def _broadcast(msg: str) -> None:
    dead: set[WebSocket] = set()
    for ws in list(_clients):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _clients -= dead
```

### Understand the Code Line by Line

---

```python
import base64
```

**`base64`** — Python's built-in base64 encoding module. Converts binary data (JPEG bytes) to a text-safe ASCII string that can be embedded in JSON.

**Why base64?** JSON is a text format. You cannot embed raw binary bytes in a JSON string. Base64 encodes each 3 bytes as 4 printable characters, increasing size by ~33% but making it JSON-embeddable.

---

```python
_clients: set[WebSocket] = set()
```

**`set[WebSocket]`** — a set (unordered, no duplicates) of WebSocket connection objects.

**Why a `set` and not a `list`?** Sets have O(1) membership testing and removal. `_clients.discard(websocket)` and `dead -= ...` operations are instant regardless of how many clients are connected. A list would require O(n) scanning.

**Module-level variable** — `camera_feed()` adds to this set; `start_broadcaster()` reads from it. Both are in the same module so they share this set directly.

---

```python
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
```

**`_clients.add(websocket)`** — registers this client so the broadcaster can send frames to it.

**`while True: await websocket.receive_text()`** — keeps the coroutine alive. `receive_text()` suspends until a text message arrives. React never sends text to `/ws/feed`, so this just waits indefinitely. When React disconnects, `receive_text()` raises `WebSocketDisconnect`.

**Why wait in a loop rather than `await asyncio.sleep(float('inf'))`?** `receive_text()` responds correctly to disconnect events. An infinite sleep would never detect that the client has gone away.

**`_clients.discard(websocket)`** — removes the client from the set. `discard` (unlike `remove`) does not raise `KeyError` if the element is not in the set.

---

```python
async def start_broadcaster() -> None:
    loop = asyncio.get_event_loop()
    prev_time = time.time()
```

**`asyncio.get_event_loop()`** — gets the running asyncio event loop. Stored in `loop` so it can be used to call `loop.run_in_executor()` below.

**`prev_time = time.time()`** — initialised before the loop so the first FPS calculation has a valid reference point.

---

```python
        ok, frame = await loop.run_in_executor(None, active.read)
```

**`loop.run_in_executor(None, active.read)`** — runs `active.read()` in a thread pool without blocking the asyncio event loop.

**`None`** — use the default thread pool executor (Python's `ThreadPoolExecutor`).

**Why a thread pool?** `active.read()` calls `cv2.VideoCapture.read()` for local cameras, which blocks the calling thread for ~33ms (the duration of one camera frame). If called directly in the asyncio loop (without `run_in_executor`), this 33ms block prevents all other WebSocket handlers from running. With `run_in_executor`, the block happens in a worker thread, and asyncio continues handling other connections.

---

```python
        if not ok:
            if frame is None:
                await asyncio.sleep(0.01)
                continue
            else:
                registry.remove(active.device_id)
                continue
```

**Three-state protocol:**
- `(True, frame)` — success, encode and broadcast below.
- `(False, None)` — `RemoteCamera` queue was empty. Wait 10ms and try again.
- `(False, non-None)` — `LocalCamera` hardware failure. Remove from registry. The next iteration picks up whatever camera becomes active.

---

```python
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, config.FEED_JPEG_QUALITY]
        _, buf = cv2.imencode(".jpg", frame, encode_params)
```

**`cv2.imencode(".jpg", frame, params)`** — encodes the NumPy BGR frame as a JPEG binary blob in memory. Returns `(success_bool, encoded_array)`.

**`_`** — the first return value (success bool) is discarded. If encoding fails, `buf` will be wrong anyway, but for a valid frame this rarely fails.

**`encode_params`** — `[cv2.IMWRITE_JPEG_QUALITY, 80]` is a flat list alternating property ID and value. This is OpenCV's API for image encoding parameters.

---

```python
        b64 = base64.b64encode(buf.tobytes()).decode("ascii")
```

**`buf.tobytes()`** — converts the OpenCV encoded array to a Python `bytes` object.

**`base64.b64encode(...)`** — encodes the bytes as base64, returning a `bytes` object of ASCII characters.

**`.decode("ascii")`** — converts the base64 `bytes` to a Python `str`. This is needed for `json.dumps()`, which requires strings.

---

```python
        msg = json.dumps({
            "type":  "frame",
            "frame": b64,
            "label": active.label,
            "fps":   fps,
        })
```

**`json.dumps()`** — converts the Python dict to a JSON string. The React frontend parses this with `JSON.parse(event.data)`.

**`"type": "frame"`** — React checks `msg.type === "frame"` to distinguish frame messages from other message types like `"no_camera"`.

---

```python
async def _broadcast(msg: str) -> None:
    dead: set[WebSocket] = set()
    for ws in list(_clients):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _clients -= dead
```

**`for ws in list(_clients)`** — iterates a copy of `_clients`. If `_clients` were modified during iteration (by a concurrent coroutine running between `await` points), iterating the original set could raise `RuntimeError`. The `list()` copy is safe.

**`dead.add(ws)`** — if `send_text()` throws (client disconnected without proper close handshake, network error), the WebSocket is added to `dead` rather than removed immediately. This avoids modifying `_clients` during iteration.

**`_clients -= dead`** — set subtraction: removes all elements in `dead` from `_clients` in one operation after the loop finishes.

---

## Step 11 — Backend Entry Point

**Goal:** Create the FastAPI application object, wire all routers, open the local camera on startup, and start the broadcaster task.

**File:** `backend/main.py` — **NEW**

### Complete Code

```python
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import backend.config as config
from backend.api import feed, routes
from backend.camera.local import LocalCamera
from backend.devices.registry import registry
from backend.transport import ws_receiver


@asynccontextmanager
async def lifespan(app: FastAPI):
    local_cam = LocalCamera()
    if local_cam.open():
        registry.add(local_cam)
    else:
        print(
            "[HTS] WARNING: No local camera found.\n"
            "      Running in remote-only mode."
        )

    broadcaster_task = asyncio.create_task(feed.start_broadcaster())

    print("\n" + "=" * 56)
    print("  HTS — Multi-Device Camera Backend")
    print("=" * 56)
    print(f"  Backend API:      http://localhost:{config.BACKEND_PORT}")
    print(f"  Remote streamer:  http://{config.LOCAL_IP}:{config.BACKEND_PORT}/api/streamer")
    print(f"  Open React UI:    http://localhost:5173")
    print("=" * 56 + "\n")

    yield

    broadcaster_task.cancel()
    try:
        await broadcaster_task
    except asyncio.CancelledError:
        pass
    registry.release_all()
    print("[HTS] Backend shut down cleanly.")


app = FastAPI(title="HTS Backend", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router,      prefix="/api")
app.include_router(feed.router)
app.include_router(ws_receiver.router)
```

### Understand the Code Line by Line

---

```python
from contextlib import asynccontextmanager
```

**`asynccontextmanager`** — a decorator that converts an `async` generator function into a context manager. This is how FastAPI's modern `lifespan` pattern works.

---

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... startup code ...
    yield
    # ... shutdown code ...
```

**`@asynccontextmanager`** — marks `lifespan` as a context manager. FastAPI calls this when the application starts and stops.

**`app: FastAPI`** — FastAPI passes the application object as the argument. Not used in this implementation, but required by the interface.

**Code before `yield`** — runs once when the server starts (after uvicorn binds the port).

**`yield`** — the application runs here. FastAPI serves requests between `yield` and the shutdown code.

**Code after `yield`** — runs when the server receives a shutdown signal (Ctrl+C or SIGTERM).

---

```python
    broadcaster_task = asyncio.create_task(feed.start_broadcaster())
```

**`asyncio.create_task()`** — schedules `feed.start_broadcaster()` to run concurrently as a background asyncio task. It starts running immediately (at the next `await` point).

**Why not `await feed.start_broadcaster()`?** `await` would run the broadcaster to completion before continuing — but `start_broadcaster()` is an infinite loop. Using `create_task` lets it run concurrently while the `lifespan` function proceeds to `yield`.

---

```python
    yield
```

**What happens here:** The FastAPI server is fully initialised and serving requests. This `yield` suspends the `lifespan` coroutine until the server is shutting down.

---

```python
    broadcaster_task.cancel()
    try:
        await broadcaster_task
    except asyncio.CancelledError:
        pass
```

**`broadcaster_task.cancel()`** — sends a cancellation request to the broadcaster task. On the next `await` inside `start_broadcaster`, `asyncio.CancelledError` is raised.

**`await broadcaster_task`** — waits for the task to actually finish after cancellation.

**`except asyncio.CancelledError: pass`** — a cancelled task raises `CancelledError` when awaited. This is expected and intentional — `pass` silently acknowledges it.

**Why cancel cleanly?** Abruptly killing the broadcaster without `cancel()` + `await` leaves it running in the background even after the server appears stopped, consuming CPU and camera resources.

---

```python
app = FastAPI(title="HTS Backend", version="2.0.0", lifespan=lifespan)
```

**`title="HTS Backend"`** — shown in the auto-generated API documentation at `/docs`.

**`lifespan=lifespan`** — registers the lifecycle manager. FastAPI calls it on startup and shutdown.

**`app`** — this module-level variable is what uvicorn imports: `uvicorn backend.main:app`.

---

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

**`CORSMiddleware`** — Cross-Origin Resource Sharing middleware. When React (on `http://localhost:5173`) sends requests to the backend (on `http://localhost:8000`), the browser blocks these by default because they are different origins. CORS headers tell the browser "this server allows requests from any origin."

**`allow_origins=["*"]`** — allow requests from all origins. For a DRDO deployment, replace with the specific frontend URL: `["http://192.168.1.x:5173"]`.

---

```python
app.include_router(routes.router, prefix="/api")
```

**`prefix="/api"`** — prepends `/api` to every route in `routes.router`. So `@router.get("/devices")` becomes accessible at `GET /api/devices`.

**`feed.router` and `ws_receiver.router`** — included without prefix, so their routes are at `/ws/feed` and `/ws/device` directly.

---

## Step 12 — Backend Dependencies

**File:** `backend/requirements.txt` — **NEW**

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
opencv-python>=4.8.0
numpy>=1.24.0
```

**`fastapi`** — the web framework. Includes Starlette (which provides WebSocket support).

**`uvicorn[standard]`** — the ASGI server. The `[standard]` extra installs `uvloop` (faster event loop on Linux) and `websockets` (for WebSocket support).

**`>=` version constraints** — "install this version or newer." Using `>=` instead of `==` lets pip resolve compatible versions if other packages require different versions.

**Install command:**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

---

## Step 13 — Test the Backend Alone

**Start the backend:**
```powershell
.\venv\Scripts\Activate.ps1
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**`--host 0.0.0.0`** — listen on all network interfaces, not just `localhost`. This is required so remote devices on the LAN can connect to the backend.

**`--reload`** — restarts the server automatically when any Python file changes. Remove this in production.

**Test checklist:**

| URL | Expected response |
|-----|-------------------|
| `http://localhost:8000/api/devices` | JSON array with local camera |
| `http://localhost:8000/docs` | Interactive API documentation |
| `http://localhost:8000/api/streamer` | Remote camera streamer HTML page |

---

## Step 14 — Create the React Frontend

**Commands:**
```powershell
npm create vite@latest frontend -- --template react
cd frontend
npm install
mkdir src\components
mkdir src\hooks
mkdir src\services
```

**`npm create vite@latest frontend`** — creates a new Vite project in the `frontend/` directory using the React template.

**`-- --template react`** — the `--` separates npm arguments from the Vite script arguments. `--template react` tells Vite to generate a React project.

**`npm install`** — downloads all dependencies listed in the generated `package.json` into `frontend/node_modules/`.

---

## Step 15 — Vite Configuration

**Goal:** Tell Vite's development server to forward API and WebSocket requests to the Python backend. This avoids CORS issues and means the same URL paths work in both development and production.

**File:** `frontend/vite.config.js` — **MODIFIED**

### Complete Code

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
```

### Understand the Code Line by Line

---

```javascript
import { defineConfig } from 'vite'
```

**`defineConfig`** — a Vite helper function that provides TypeScript autocomplete for the config object. Functionally equivalent to `export default { ... }` but enables editor type-checking.

---

```javascript
import react from '@vitejs/plugin-react'
```

**`@vitejs/plugin-react`** — Vite plugin that enables JSX transformation (converting `<Component />` syntax to `React.createElement()`) and React Fast Refresh (live reload that preserves component state during development).

---

```javascript
  plugins: [react()],
```

**`react()`** — calls the plugin factory to create the plugin instance. The plugin is then passed to Vite's plugin system.

---

```javascript
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
```

**`'/api'`** — any request from React to a URL starting with `/api` will be proxied.

**`target: 'http://localhost:8000'`** — forward the request to the backend at this address.

**`changeOrigin: true`** — changes the `Host` header in the proxied request to match the target. Required for some server configurations that validate the `Host` header.

**Effect:** `fetch('/api/devices')` in React → Vite intercepts → sends `GET http://localhost:8000/api/devices` → gets response → returns it to React. The browser never directly contacts port 8000.

---

```javascript
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
```

**`ws: true`** — tells Vite this proxy entry handles WebSocket connections, not just HTTP.

**`target: 'ws://localhost:8000'`** — forward WebSocket connections to the backend.

**Effect:** `new WebSocket('ws://localhost:5173/ws/feed')` in React → Vite proxies the WS upgrade request to `ws://localhost:8000/ws/feed` → establishes a tunnel → all WebSocket messages pass through Vite transparently.

---

## Step 16 — API Service Layer

**Goal:** Centralise all HTTP calls to the backend in one file. Components call these functions — they never use `fetch()` directly.

**File:** `frontend/src/services/api.js` — **NEW**

### Complete Code

```javascript
export async function getDevices() {
  const res = await fetch('/api/devices');
  if (!res.ok) throw new Error(`GET /api/devices failed: ${res.status}`);
  return res.json();
}

export async function setActiveDevice(deviceId) {
  const res = await fetch(`/api/devices/${deviceId}/active`, { method: 'POST' });
  if (!res.ok) throw new Error(`POST .../active failed: ${res.status}`);
  return res.json();
}

export async function disconnectDevice(deviceId) {
  const res = await fetch(`/api/devices/${deviceId}/disconnect`, { method: 'POST' });
  if (!res.ok) throw new Error(`POST .../disconnect failed: ${res.status}`);
  return res.json();
}

export function getStreamerPageUrl() {
  return '/api/streamer';
}
```

### Understand the Code Line by Line

---

```javascript
export async function getDevices() {
```

**`export`** — makes this function importable in other files: `import { getDevices } from '../services/api'`.

**`async function`** — this function returns a `Promise`. Callers can `await` it or chain `.then()`. The `await fetch(...)` inside uses the async context.

---

```javascript
  const res = await fetch('/api/devices');
```

**`fetch('/api/devices')`** — the browser's built-in HTTP client. Sends a `GET` request to `/api/devices`. Because Vite is proxying, this actually goes to `http://localhost:8000/api/devices`.

**`await`** — waits for the HTTP response headers to arrive. `res` is a `Response` object.

**Note:** `await fetch()` does not throw on HTTP errors (404, 500). It only throws on network failures (no connection). HTTP errors must be detected via `res.ok`.

---

```javascript
  if (!res.ok) throw new Error(`GET /api/devices failed: ${res.status}`);
```

**`res.ok`** — `true` if HTTP status is in 200–299 range.

**`throw new Error(...)`** — propagates the error to the caller. Callers should wrap the call in `try/catch`. In `DevicePanel.jsx`, the `catch` block is empty (`catch { }`) because a polling failure is silently retried on the next poll.

---

```javascript
  return res.json();
```

**`res.json()`** — reads the response body as JSON. Returns a `Promise` that resolves to the parsed JavaScript object. The `async function` wrapping allows returning this `Promise` directly — callers `await getDevices()` and get the array.

---

```javascript
export function getStreamerPageUrl() {
  return '/api/streamer';
}
```

**Why a function instead of a constant?** Allows future implementations to compute the URL dynamically (e.g., based on environment variables or window.location). Currently returns a fixed string.

---

## Step 17 — Camera Feed Hook

**Goal:** Manage the WebSocket connection to `/ws/feed` and deliver frames to any React component. Components call `useCameraFeed()` and get `{ frame, fps, label, connected }` — no WebSocket code in components.

**File:** `frontend/src/hooks/useCameraFeed.js` — **NEW**

### Complete Code

```javascript
import { useState, useEffect, useRef } from 'react';

export function useCameraFeed() {
  const [frame,     setFrame]     = useState(null);
  const [fps,       setFps]       = useState(0);
  const [label,     setLabel]     = useState('');
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      if (cancelled) return;
      const ws = new WebSocket(`ws://${window.location.host}/ws/feed`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!cancelled) setConnected(true);
      };

      ws.onclose = () => {
        if (!cancelled) {
          setConnected(false);
          setFrame(null);
          setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (event) => {
        if (cancelled) return;
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'frame') {
            setFrame(msg.frame);
            setFps(msg.fps);
            setLabel(msg.label);
          } else if (msg.type === 'no_camera') {
            setFrame(null);
            setLabel('');
          }
        } catch {
          // ignore malformed messages
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { frame, fps, label, connected };
}
```

### Understand the Code Line by Line

---

```javascript
import { useState, useEffect, useRef } from 'react';
```

**`useState`** — React hook for state variables. When state changes, the component re-renders.

**`useEffect`** — React hook for side effects (opening a WebSocket, subscribing to events, etc.). Runs after the component mounts.

**`useRef`** — React hook for a mutable reference that persists across renders without causing re-renders. Used to store the WebSocket object.

---

```javascript
  const [frame, setFrame] = useState(null);
```

**`useState(null)`** — creates a state variable `frame` with initial value `null`. `setFrame` is the setter function. Calling `setFrame(newValue)` causes React to re-render any component using this hook.

**`null` initial value** — while no frame has arrived, `frame` is `null`. `CameraFeed.jsx` checks `if (frame)` to show the placeholder.

---

```javascript
  const wsRef = useRef(null);
```

**`useRef(null)`** — creates a ref object `{ current: null }`. The WebSocket is stored as `wsRef.current`. Unlike state, changing `wsRef.current` does not trigger a re-render.

**Why `useRef` for the WebSocket?** The WebSocket object must survive across re-renders (state changes cause re-renders, but we do not want to re-create the WebSocket). A `ref` persists through re-renders while a plain variable would be reset.

---

```javascript
  useEffect(() => {
    let cancelled = false;
    ...
    return () => {
      cancelled = true;
      if (wsRef.current) wsRef.current.close();
    };
  }, []);
```

**`useEffect(..., [])`** — the empty array `[]` means "run this effect only once, after the component first mounts." Without the array, the effect would run after every re-render, creating a new WebSocket on every frame update.

**`let cancelled = false`** — a flag that becomes `true` when the component unmounts.

**`return () => { ... }`** — the cleanup function. React calls it when the component unmounts (user navigates away, or React Strict Mode double-invokes effects in development). Sets `cancelled = true` to prevent the reconnect logic from firing after unmount.

---

```javascript
      const ws = new WebSocket(`ws://${window.location.host}/ws/feed`);
```

**`window.location.host`** — the hostname and port of the current page, e.g., `"localhost:5173"`. This automatically uses the correct host whether in development (Vite) or production (any server).

**`ws://`** — plain WebSocket (not encrypted). For production HTTPS deployments, use `wss://`.

**Result:** `"ws://localhost:5173/ws/feed"` — Vite proxies this to `ws://localhost:8000/ws/feed`.

---

```javascript
      ws.onclose = () => {
        if (!cancelled) {
          setConnected(false);
          setFrame(null);
          setTimeout(connect, 2000);
        }
      };
```

**`setTimeout(connect, 2000)`** — schedules `connect()` to run again after 2 seconds. This implements automatic reconnection if the backend restarts during development.

**`if (!cancelled)`** — without this check, if the component unmounts and the WebSocket closes, `setTimeout` would schedule a new connection attempt on an unmounted component, causing React state update warnings.

---

```javascript
          const msg = JSON.parse(event.data);
          if (msg.type === 'frame') {
            setFrame(msg.frame);
            setFps(msg.fps);
            setLabel(msg.label);
          }
```

**`event.data`** — the string data of the received WebSocket message (JSON sent by the broadcaster).

**`JSON.parse(event.data)`** — converts the JSON string back to a JavaScript object.

**`setFrame(msg.frame)`** — `msg.frame` is the base64-encoded JPEG string. Setting state triggers a re-render of `CameraFeed.jsx` which renders the new frame.

---

## Step 18 — Status Bar Component

**File:** `frontend/src/components/StatusBar.jsx` — **NEW**

### Complete Code

```jsx
export default function StatusBar({ connected, deviceCount }) {
  return (
    <div className="status-bar">
      <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`} />
      <span className="status-text">
        {connected
          ? `Backend connected — ${deviceCount} device${deviceCount !== 1 ? 's' : ''}`
          : 'Connecting to backend…'}
      </span>
    </div>
  );
}
```

### Understand the Code Line by Line

---

```jsx
export default function StatusBar({ connected, deviceCount }) {
```

**`export default`** — makes this the default export of the file. Imported as `import StatusBar from './components/StatusBar'`.

**`{ connected, deviceCount }`** — destructuring the `props` object. Instead of `props.connected`, we write `connected` directly. These values come from the parent component `App.jsx`.

---

```jsx
      <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`} />
```

**`className`** — React uses `className` instead of `class` because `class` is a reserved keyword in JavaScript.

**Template literal** — `` `status-dot ${...}` `` builds the string `"status-dot connected"` or `"status-dot disconnected"` depending on the `connected` state. CSS rules for `.connected` and `.disconnected` in `App.css` set the dot colour.

**`?:`** — JavaScript ternary operator: `condition ? valueIfTrue : valueIfFalse`.

---

```jsx
          ? `Backend connected — ${deviceCount} device${deviceCount !== 1 ? 's' : ''}`
```

**`deviceCount !== 1 ? 's' : ''`** — pluralisation: "1 device" vs "2 devices". When `deviceCount` is 1, the `s` is omitted.

---

## Step 19 — Device Panel Component

**Goal:** Show the list of connected devices, allow switching the active camera, and allow disconnecting devices.

**File:** `frontend/src/components/DevicePanel.jsx` — **NEW**

### Complete Code

```jsx
import { useState, useEffect } from 'react';
import { getDevices, setActiveDevice, disconnectDevice, getStreamerPageUrl } from '../services/api';

export default function DevicePanel({ onDeviceCountChange }) {
  const [devices,    setDevices]    = useState([]);
  const [loading,    setLoading]    = useState(false);
  const [streamerUrl] = useState(getStreamerPageUrl);

  useEffect(() => {
    let active = true;

    async function fetchDevices() {
      try {
        const data = await getDevices();
        if (active) {
          setDevices(data);
          onDeviceCountChange?.(data.length);
        }
      } catch {
        // backend not ready, retry on next poll
      }
    }

    fetchDevices();
    const id = setInterval(fetchDevices, 2000);
    return () => { active = false; clearInterval(id); };
  }, [onDeviceCountChange]);

  async function handleSetActive(deviceId) {
    setLoading(true);
    try { await setActiveDevice(deviceId); } catch { /* ignore */ }
    setLoading(false);
  }

  async function handleDisconnect(deviceId) {
    setLoading(true);
    try { await disconnectDevice(deviceId); } catch { /* ignore */ }
    setLoading(false);
  }

  return (
    <div className="device-panel">
      <h2>Device Manager</h2>

      <div className="remote-url-box">
        <p className="remote-url-label">Connect a remote device:</p>
        <p className="remote-url-hint">Open this URL in any browser on the same network:</p>
        <a href={streamerUrl} target="_blank" rel="noreferrer" className="remote-url-link">
          {window.location.hostname}:8000/api/streamer
        </a>
        <p className="remote-url-hint">Or check the backend terminal for the exact LAN URL.</p>
      </div>

      <div className="devices-section">
        <h3>Connected Devices</h3>
        {devices.length === 0 ? (
          <p className="no-devices">No cameras connected.</p>
        ) : (
          <ul className="device-list">
            {devices.map(dev => (
              <li key={dev.id} className={`device-item ${dev.is_active ? 'active' : ''}`}>
                <div className="device-info">
                  <span className={`device-status-dot ${dev.is_open ? 'open' : 'closed'}`} />
                  <div>
                    <p className="device-label">{dev.label}</p>
                    <p className="device-meta">
                      {dev.width > 0 ? `${dev.width}×${dev.height}` : 'Waiting for stream…'}
                      {dev.is_active && ' · ACTIVE'}
                    </p>
                  </div>
                </div>
                <div className="device-actions">
                  {!dev.is_active && (
                    <button className="btn-view" onClick={() => handleSetActive(dev.id)} disabled={loading}>
                      View
                    </button>
                  )}
                  <button className="btn-disconnect" onClick={() => handleDisconnect(dev.id)} disabled={loading}>
                    Disconnect
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
```

### Understand the Code Line by Line

---

```jsx
  const [streamerUrl] = useState(getStreamerPageUrl);
```

**`useState(getStreamerPageUrl)`** — note: `getStreamerPageUrl` is passed without `()`. When `useState` receives a function (not a value), it calls it once to compute the initial state. This is called "lazy initialisation."

**Why not `useState(getStreamerPageUrl())`?** Both work here since the function has no side effects. The lazy form `useState(fn)` is a React optimisation for expensive computations — the function is only called once even if the component re-renders.

---

```jsx
  useEffect(() => {
    let active = true;
    async function fetchDevices() {
      try {
        const data = await getDevices();
        if (active) {
          setDevices(data);
          onDeviceCountChange?.(data.length);
        }
      } catch { }
    }
    fetchDevices();
    const id = setInterval(fetchDevices, 2000);
    return () => { active = false; clearInterval(id); };
  }, [onDeviceCountChange]);
```

**`let active = true`** — cleanup flag. Prevents state updates after the component unmounts.

**`fetchDevices()`** — called immediately on mount (first device list appears instantly).

**`setInterval(fetchDevices, 2000)`** — calls `fetchDevices` every 2000ms (2 seconds). This polls for new remote device connections.

**`clearInterval(id)`** — stops the interval when the component unmounts. Without this, the interval continues running even after the component is gone, causing React warnings about state updates on unmounted components.

**`[onDeviceCountChange]`** — dependency array. The effect re-runs if `onDeviceCountChange` changes. Since it is a function passed from `App.jsx`, this prevents the effect from running with a stale callback.

---

```jsx
  onDeviceCountChange?.(data.length);
```

**`?.`** — optional chaining. Calls `onDeviceCountChange(data.length)` only if `onDeviceCountChange` is not `null` or `undefined`. This makes the prop optional — `DevicePanel` works even if the parent does not pass `onDeviceCountChange`.

---

```jsx
            {devices.map(dev => (
              <li key={dev.id} ...>
```

**`devices.map(dev => ...)`** — React pattern for rendering a list. For each device object, returns a JSX element.

**`key={dev.id}`** — React requires a unique `key` prop when rendering lists. It uses `key` to track which list items changed, were added, or were removed, enabling efficient DOM updates. Without `key`, React re-renders the entire list on every change.

---

```jsx
              <li key={dev.id} className={`device-item ${dev.is_active ? 'active' : ''}`}>
```

**`dev.is_active ? 'active' : ''`** — adds the CSS class `"active"` to the active device's list item. In `App.css`, `.device-item.active` has a green border to visually highlight the current camera.

---

```jsx
                  {!dev.is_active && (
                    <button ...>View</button>
                  )}
```

**`{!dev.is_active && (...)}` pattern** — in JSX, `{condition && <element />}` renders the element only when `condition` is truthy. The View button is hidden for the currently active device (no need to switch to a camera already showing).

---

## Step 20 — Camera Feed Component

**Goal:** Display the live video by rendering each received frame as a JPEG image.

**File:** `frontend/src/components/CameraFeed.jsx` — **NEW**

### Complete Code

```jsx
import { useCameraFeed } from '../hooks/useCameraFeed';

export default function CameraFeed() {
  const { frame, fps, label, connected } = useCameraFeed();

  return (
    <div className="camera-feed">
      {frame ? (
        <>
          <img
            src={`data:image/jpeg;base64,${frame}`}
            alt="Live camera feed"
            className="feed-image"
          />
          <div className="feed-overlay">
            <span className="feed-label">{label}</span>
            <span className="feed-fps">{fps} FPS</span>
          </div>
        </>
      ) : (
        <div className="feed-placeholder">
          {connected ? (
            <>
              <span className="placeholder-icon">📷</span>
              <p>No camera active</p>
              <p className="placeholder-hint">Select a device from the panel →</p>
            </>
          ) : (
            <>
              <span className="placeholder-icon">⏳</span>
              <p>Connecting to backend…</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
```

### Understand the Code Line by Line

---

```jsx
  const { frame, fps, label, connected } = useCameraFeed();
```

**Destructuring** — unpacks the object returned by `useCameraFeed()` into four named variables. Equivalent to:
```javascript
const result = useCameraFeed();
const frame = result.frame;
const fps = result.fps;
// ...
```

---

```jsx
          <img
            src={`data:image/jpeg;base64,${frame}`}
            alt="Live camera feed"
            className="feed-image"
          />
```

**`data:image/jpeg;base64,${frame}`** — a Data URL. The browser decodes the base64 JPEG data and renders it as an image, the same as if you linked to a file. No network request is made — the image data is already in memory.

**Why `<img>` and not `<canvas>`?** `<img>` with a `data:` URL is the simplest approach. The browser handles JPEG decoding natively and efficiently. `<canvas>` would require calling `drawImage()` with a created `Image` object on every frame — more code for the same result.

**React optimisation:** React does not re-create the `<img>` DOM element on each re-render. It only updates the `src` attribute, which the browser handles as an image replacement.

---

```jsx
      {frame ? (
        <> ... </>
      ) : (
        <div className="feed-placeholder"> ... </div>
      )}
```

**`{frame ? ... : ...}`** — ternary in JSX. When `frame` is `null` or an empty string (falsy), shows the placeholder. When `frame` is a base64 string (truthy), shows the image.

**`<>...</>`** — React Fragment. Groups multiple elements without adding a real DOM element. Required here because the `<img>` and `<div>` overlay must both be rendered but they cannot be direct children of a JSX ternary — JSX expressions must return a single root element.

---

## Step 21 — Root App Component

**File:** `frontend/src/App.jsx` — **MODIFIED**

### Complete Code

```jsx
import { useState } from 'react';
import CameraFeed  from './components/CameraFeed';
import DevicePanel from './components/DevicePanel';
import StatusBar   from './components/StatusBar';
import { useCameraFeed } from './hooks/useCameraFeed';
import './App.css';

export default function App() {
  const [deviceCount, setDeviceCount] = useState(0);
  const { connected } = useCameraFeed();

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-brand">
          <span className="brand-dot" />
          <h1>Human Tracking System</h1>
        </div>
        <StatusBar connected={connected} deviceCount={deviceCount} />
      </header>
      <main className="app-main">
        <CameraFeed />
        <DevicePanel onDeviceCountChange={setDeviceCount} />
      </main>
    </div>
  );
}
```

### Understand the Code Line by Line

---

```jsx
import './App.css';
```

**What is written?** Imports the CSS file with no variable. There is no named export.

**What does it mean?** Vite processes this import by injecting the CSS rules into the page's `<style>` tags when the app loads. All CSS classes defined in `App.css` become active for the entire page.

---

```jsx
  const { connected } = useCameraFeed();
```

**Why call `useCameraFeed()` in `App.jsx` again?** `App.jsx` needs `connected` for `StatusBar`. `CameraFeed.jsx` also calls `useCameraFeed()`. This creates two WebSocket connections to `/ws/feed`. The backend handles both — both receive the same frames. This is acceptable in Phase 1. For production, lift `useCameraFeed` to `App.jsx` and pass `frame` and `connected` as props to `CameraFeed`.

---

```jsx
        <DevicePanel onDeviceCountChange={setDeviceCount} />
```

**`onDeviceCountChange={setDeviceCount}`** — passes React's `setDeviceCount` function as a prop. When `DevicePanel` calls `onDeviceCountChange(data.length)`, it is actually calling `setDeviceCount(data.length)` in `App.jsx`. This updates `deviceCount` state in `App.jsx`, which is then passed to `StatusBar`.

**This is React's "lifting state up" pattern** — shared state lives in the lowest common ancestor component.

---

## Step 22 — Application Styles

**File:** `frontend/src/App.css` — **MODIFIED**

### Complete Code

```css
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  --bg:        #0f0f1a;
  --surface:   #1a1a2e;
  --surface2:  #22223a;
  --accent:    #00c896;
  --text:      #e0e0e0;
  --text-dim:  #888;
  --danger:    #e05050;
  --border:    #2a2a45;
  --radius:    10px;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
}

.app { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

.app-header {
  display: flex; align-items: center; justify-content: space-between;
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 0 20px; height: 52px; flex-shrink: 0;
}

.header-brand { display: flex; align-items: center; gap: 10px; }

.brand-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--accent); box-shadow: 0 0 8px var(--accent);
}

.app-header h1 { font-size: 0.95rem; font-weight: 700; }

.status-bar { display: flex; align-items: center; gap: 8px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-dot.connected    { background: var(--accent); }
.status-dot.disconnected { background: var(--text-dim); }
.status-text { font-size: 0.78rem; color: var(--text-dim); }

.app-main { display: flex; flex: 1; overflow: hidden; }

.camera-feed {
  flex: 1; display: flex; align-items: center; justify-content: center;
  background: #000; position: relative; overflow: hidden;
}

.feed-image { max-width: 100%; max-height: 100%; object-fit: contain; display: block; }

.feed-overlay {
  position: absolute; top: 12px; left: 12px;
  display: flex; gap: 14px;
  background: rgba(0,0,0,0.55); backdrop-filter: blur(4px);
  padding: 5px 12px; border-radius: 6px; font-size: 0.78rem;
}

.feed-label { color: var(--accent); font-weight: 600; }
.feed-fps   { color: var(--text-dim); }

.feed-placeholder {
  display: flex; flex-direction: column; align-items: center;
  gap: 10px; color: var(--text-dim);
}

.placeholder-icon { font-size: 3rem; opacity: 0.4; }
.placeholder-hint { font-size: 0.78rem; }

.device-panel {
  width: 320px; flex-shrink: 0;
  background: var(--surface); border-left: 1px solid var(--border);
  display: flex; flex-direction: column; overflow-y: auto;
}

.device-panel h2 {
  font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--accent); padding: 16px 16px 0;
}

.remote-url-box {
  margin: 12px 16px; background: var(--bg);
  border: 1px solid var(--border); border-radius: var(--radius); padding: 12px;
}

.remote-url-label { font-weight: 600; margin-bottom: 4px; }
.remote-url-hint  { font-size: 0.72rem; color: var(--text-dim); margin-bottom: 4px; }

.remote-url-link {
  display: block; color: var(--accent); font-size: 0.78rem;
  word-break: break-all; text-decoration: none;
  background: var(--surface); border-radius: 6px;
  padding: 6px 8px; margin-bottom: 6px;
}

.remote-url-link:hover { text-decoration: underline; }

.devices-section { padding: 0 16px 16px; flex: 1; }

.devices-section h3 {
  font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: 0.1em; color: var(--text-dim); margin: 12px 0 8px;
}

.no-devices { color: var(--text-dim); font-size: 0.85rem; padding: 8px 0; }

.device-list { list-style: none; display: flex; flex-direction: column; gap: 8px; }

.device-item {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px; transition: border-color 0.2s;
}

.device-item.active {
  border-color: var(--accent);
  background: rgba(0, 200, 150, 0.05);
}

.device-info { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; }

.device-status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
.device-status-dot.open   { background: var(--accent); }
.device-status-dot.closed { background: var(--danger); }

.device-label { font-size: 0.88rem; font-weight: 500; }
.device-meta  { font-size: 0.72rem; color: var(--text-dim); margin-top: 2px; }

.device-actions { display: flex; gap: 8px; }

button {
  padding: 6px 14px; border: none; border-radius: 6px;
  font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: opacity 0.15s;
}

button:disabled { opacity: 0.4; cursor: default; }
button:not(:disabled):hover { opacity: 0.85; }

.btn-view       { background: var(--accent); color: #000; }
.btn-disconnect { background: transparent; border: 1px solid var(--danger); color: var(--danger); }
```

### Key CSS Concepts

---

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
```

**`*`** — selects every HTML element.

**`box-sizing: border-box`** — makes `width` and `height` include padding and border. Without this, a `width: 320px` element with `padding: 12px` would be 344px wide — confusing and hard to calculate.

**`margin: 0; padding: 0`** — resets browser default spacing. Browsers add default margins to `<h1>`, `<p>`, etc. Resetting them gives a consistent starting point.

---

```css
:root { --bg: #0f0f1a; ... }
```

**`:root`** — matches the `<html>` element. CSS custom properties (variables) defined here are available everywhere.

**`--bg`, `--accent`, etc.** — CSS custom properties (variables). Used as `var(--bg)` elsewhere. Changing `--accent: #00c896` to another colour updates the entire application's accent colour from one line.

---

```css
.app { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
```

**`display: flex`** — activates Flexbox layout.

**`flex-direction: column`** — stacks children vertically: header on top, `main` below.

**`height: 100vh`** — makes the app exactly the viewport height. `vh` = viewport height units. The app fills the entire browser window.

**`overflow: hidden`** — prevents any content from scrolling outside the app boundary.

---

```css
.app-main { display: flex; flex: 1; overflow: hidden; }
```

**`flex: 1`** — makes `main` take all remaining height after the header. `flex: 1` is shorthand for `flex-grow: 1; flex-shrink: 1; flex-basis: 0`.

**`display: flex`** — creates a horizontal row inside `main`: camera feed on the left, device panel on the right.

---

```css
.camera-feed { flex: 1; ... }
.device-panel { width: 320px; flex-shrink: 0; ... }
```

**`flex: 1` on `.camera-feed`** — takes all available width except what `.device-panel` uses.

**`flex-shrink: 0` on `.device-panel`** — prevents the panel from shrinking below its 320px width even if the window is narrow.

---

## Step 23 — React Entry Point

**File:** `frontend/src/main.jsx` — **MODIFIED**

### Complete Code

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### Understand the Code Line by Line

---

```jsx
import { createRoot } from 'react-dom/client'
```

**`react-dom/client`** — the React DOM rendering package for React 18+. Provides `createRoot`, the entry point for the new concurrent rendering mode.

---

```jsx
createRoot(document.getElementById('root'))
```

**`document.getElementById('root')`** — finds the `<div id="root">` element in `index.html`. This is where React mounts the entire application.

**`createRoot(...)`** — creates a React root (React 18 API). Enables concurrent mode features like automatic batching and `Suspense`.

---

```jsx
.render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

**`.render(...)`** — renders the JSX tree into the root element.

**`<StrictMode>`** — React development tool. In development, it intentionally renders components twice to detect side effects. In production builds, `StrictMode` has no effect. This is why `useEffect` seems to run twice in development — normal behaviour.

---

## Step 24 — HTML Shell

**File:** `frontend/index.html` — **MODIFIED**

### Complete Code

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Human Tracking System — Multi-Device Camera Viewer" />
    <title>HTS — Human Tracking System</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

### Understand the Code Line by Line

---

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
```

**`width=device-width`** — sets the viewport width to the device's screen width, not a default 980px. Without this, mobile browsers zoom out the desktop layout.

**`initial-scale=1.0`** — no initial zoom. The page appears at its natural size.

---

```html
    <div id="root"></div>
```

**`id="root"`** — the mount point. React's `createRoot(document.getElementById('root'))` in `main.jsx` finds this element and renders the entire React application inside it.

**Why empty?** React fills it dynamically. Before React renders (for a few milliseconds), the page is blank. For production, you could add a loading spinner here.

---

```html
    <script type="module" src="/src/main.jsx"></script>
```

**`type="module"`** — tells the browser to load this script as an ES Module. Modules support `import`/`export` syntax. Vite intercepts this during development and transforms JSX and module imports. In production, Vite replaces this with a reference to the built JavaScript bundle.

---

## Step 25 — Full Integration Test

### Start the backend

```powershell
# Terminal 1 — project root
.\venv\Scripts\Activate.ps1
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start the React frontend

```powershell
# Terminal 2 — frontend directory
cd frontend
npm run dev
```

Open `http://localhost:5173` in the browser.

### Integration checklist

| # | Test | Expected |
|---|------|----------|
| 1 | React opens | Dark UI, header, camera feed, device panel |
| 2 | Status bar | "Backend connected — 1 device" |
| 3 | Camera feed | Local webcam visible with FPS overlay |
| 4 | Device panel | Shows "Local Camera (index 0)" row with green dot |
| 5 | Remote device | Open `http://192.168.1.x:8000/api/streamer` on phone |
| 6 | Start Streaming | Device panel shows new device within 2 seconds |
| 7 | Click View | Feed switches to phone camera immediately |
| 8 | Click Disconnect | Device disappears from list; feed returns to local |
| 9 | Close browser tab | Device removed within 2 seconds |
| 10 | Ctrl+C backend | "Backend shut down cleanly." printed |

---

# Part 4 — Architecture and Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│               REMOTE DEVICE  (any modern browser)           │
│  getUserMedia() → canvas → JPEG → WebSocket binary          │
└──────────────────────────┬──────────────────────────────────┘
                           │  WS /ws/device (binary JPEG frames)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 PYTHON BACKEND  (FastAPI)                   │
│                                                             │
│  ws_receiver.py          transport/static/streamer.html     │
│    np.frombuffer()       Served by routes.py                │
│    cv2.imdecode()        with {{WS_HOST}} injected          │
│    RemoteCamera                                             │
│    .push_frame()                                            │
│         │                                                   │
│  LocalCamera  ──────────────┐                               │
│  cv2.VideoCapture           ▼                               │
│                        DeviceRegistry                       │
│                        (singleton)                          │
│                        .get_active()                        │
│                             │                               │
│  feed.py                    │                               │
│  start_broadcaster()        │                               │
│    run_in_executor──────────┘                               │
│    active.read()                                            │
│    cv2.imencode()                                           │
│    base64.b64encode()                                       │
│         │                                                   │
│  routes.py                  │  WS /ws/feed                  │
│  GET /api/devices            │  JSON {type,frame,fps,label} │
│  POST /api/.../active        │                              │
│  POST /api/.../disconnect    │                              │
│  CameraFeed.jsx                                             │
│    <img src={`data:image/jpeg;base64,${frame}`} />          │
│                                                             │
│  DevicePanel.jsx                                            │
│    setInterval(getDevices, 2000)                            │
│    onClick → setActiveDevice(id)                            │
│    onClick → disconnectDevice(id)                           │
└─────────────────────────────────────────────────────────────┘
```

---

# Part 5 — Dependencies

## Python

| Package | Purpose |
|---------|---------|
| `fastapi` | HTTP + WebSocket server, REST API routing |
| `uvicorn[standard]` | ASGI server to run FastAPI |
| `opencv-python` | Camera capture, frame decode/encode, JPEG compression |
| `numpy` | Frame array operations (required by OpenCV) |

## JavaScript (Frontend)

| Package | Purpose |
|---------|---------|
| `react`, `react-dom` | UI component system and DOM rendering |
| `vite`, `@vitejs/plugin-react` | Dev server, JSX transform, build tool |

---

# Part 6 — Current Status

## Implemented System Status

| Feature | Status |
|---------|--------|
| `backend/` folder structure | ✅ Implemented |
| Camera abstraction layer (`CameraSource`) | ✅ Implemented |
| Device registry (`DeviceRegistry`) | ✅ Implemented |
| WebSocket receiver (`/ws/device`) | ✅ Implemented |
| Browser streamer page (`streamer.html`) | ✅ Implemented & Fixed Secure Context Flow |
| FastAPI backend (`main.py`, `routes.py`, `feed.py`, `certs.py`) | ✅ Implemented & HTTPS Enabled |
| React frontend (`Vite`, `App`, `DevicePanel`, `CameraFeed`) | ✅ Implemented & HTTPS LAN Support |
| Local camera feed display & resilience | ✅ Implemented & Verified |
| Multi-device switching | ✅ Implemented & Verified |
| HTTPS Remote Streamer & Secure Context | ✅ Implemented & Verified |

---

# Part 7 — Fixes & Architecture Updates

## Overview of System Fixes

This section documents the major bug fixes and architectural enhancements applied to the Human Tracking System to ensure robust multi-device camera streaming, secure HTTPS remote device access, proper browser permission handling, and reliable local hardware display.


---

## Flow 1 — Camera Permission Flow Diagram

```
User opens remote streamer page (http://<IP>:8000/api/streamer)
        │
        ▼
Camera does NOT start automatically (page remains idle)
        │
        ▼
User clicks "Start Streaming" button
        │
        ▼
navigator.mediaDevices.getUserMedia({ video: true }) is invoked
        │
        ▼
Browser displays native permission prompt (Allow / Deny)
        ├──► User clicks ALLOW:
        │      │
        │      ▼
        │    Camera stream acquired → attached to <video> preview
        │      │
        │      ▼
        │    WebSocket opened to ws://<IP>:8000/ws/device
        │      │
        │      ▼
        │    Init message sent: {"type": "init", "name": "..."}
        │      │
        │      ▼
        │    JPEG frames encoded & streamed via requestAnimationFrame
        │      │
        │      ▼
        │    UI updates: Badge "● LIVE", Status "Streaming to laptop"
        │
        └──► User clicks DENY:
               │
               ▼
             getUserMedia promise rejects with NotAllowedError
               │
               ▼
             Error caught cleanly without crashing
               │
               ▼
             Status updates: "Camera access denied. Please allow camera permissions..."
               │
               ▼
             "Start Streaming" button remains enabled & clickable
               │
               ▼
             User changes browser site settings to "Allow" and clicks "Start Streaming" again
```

---

## Flow 2 — Local Laptop Camera Initialization & Display Flow Diagram

```
Application starts (uvicorn backend.main:app)
        │
        ▼
LocalCamera instantiated & open() executed
        │
        ▼
Candidate loop scans indices [0, 1, 2, 3, 4] with cv2.CAP_DSHOW
        │
        ▼
cap.isOpened() checked AND ok, frame = cap.read() verified
(Guarantees index actually outputs valid frames before selection)
        │
        ▼
Local camera registered in DeviceRegistry as "local:0"
        │
        ▼
registry._active_id set to "local:0" (default active camera)
        │
        ▼
React frontend mounts & connects WebSocket to /ws/feed
        │
        ▼
Broadcaster task in feed.py calls active.read() in thread pool
        │
        ▼
Transient frame drops handled gracefully (up to 10 retries before marking disconnected)
        │
        ▼
Valid BGR frame encoded to JPEG -> base64 -> JSON payload
        │
        ▼
React receives msg.type === "frame" and renders <img src="data:image/jpeg;base64,...">
        │
        ▼
Live laptop webcam feed displayed seamlessly on main UI
```

---

## Flow 3 — Device Switching Flow Diagram

```
[Local Camera Active]
Main display shows live feed of "Local Camera (index 0)"
        │
        ▼
Remote phone connects via streamer page & starts streaming
        │
        ▼
ws_receiver adds RemoteCamera to DeviceRegistry
        │
        ▼
React polls /api/devices (every 2s or on-demand)
DevicePanel shows new device: "Phone Camera (192.168.1.15)"
        │
        ▼
User clicks "View" button next to "Phone Camera"
        │
        ▼
React calls POST /api/devices/{phone_id}/active
        │
        ▼
DeviceRegistry.set_active(phone_id) updates _active_id to phone_id
React immediately fetches updated device list & updates active highlight
        │
        ▼
feed.py broadcaster reads next frame from RemoteCamera queue
        │
        ▼
Main display immediately updates to show "Phone Camera" live feed
        │
        ▼
User clicks "View" button next to "Local Camera (index 0)"
        │
        ▼
React calls POST /api/devices/local:0/active
        │
        ▼
DeviceRegistry updates _active_id back to "local:0"
        │
        ▼
Main display immediately switches back to laptop webcam feed
```

---

## Detailed Root Cause Analysis: Local Camera "No Camera Active" Bug

### Problem Statement
The Device Manager sidebar listed `"Local Camera (index 0)"` as `ACTIVE`, but the main view displayed `"No camera active"`.

### Cause Identification
1. **Unverified Camera Selection**: `LocalCamera.open()` previously checked `cap.isOpened()` but did not test reading an actual frame (`cap.read()`). On Windows systems with DirectShow drivers, virtual cameras or inactive hardware indices can report `isOpened() == True` while failing when `cap.read()` is called.
2. **Fragile Failure Handling**: In `LocalCamera.read()`, a single `ok == False` returned `(False, b"")`. In `feed.py`, `(False, b"")` was treated as a permanent fatal hardware error, instantly removing `local:0` from the `DeviceRegistry` and clearing `_active_id`.
3. **Broadcaster State Disconnect**: Once `_active_id` became `None`, `feed.py` broadcasted `{"type": "no_camera"}` over the WebSocket. React received `"no_camera"` and cleared `frame` state to `null`, rendering the `"No camera active"` placeholder.
4. **WebSocket Hook Multiplication**: Both `App.jsx` and `CameraFeed.jsx` independently called `useCameraFeed()`, opening two parallel WebSocket connections to `/ws/feed`.

### Solution Applied
1. **Hardware Frame Verification**: `LocalCamera.open()` now reads a test frame (`ok, test_frame = cap.read()`) during index scanning.
2. **Consecutive Retry Threshold**: `LocalCamera.read()` tracks `_consecutive_failures`. Transient dropped frames return `(False, None)` (non-fatal, allowing `feed.py` to sleep 10ms and retry). Only after **10 consecutive failures** is a hardware disconnect declared.
3. **Single Hook Lift**: `useCameraFeed()` was lifted to `App.jsx`, ensuring a single shared WebSocket connection passes feed state down to components as props.
4. **Instant Action Refresh**: `DevicePanel.jsx` re-fetches device status immediately after posting `setActiveDevice` or `disconnectDevice`, keeping UI active highlights synchronized.

---

## Complete Modified Source Files & Explanations

---

### Modified File 1: `backend/transport/static/streamer.html`

**Purpose:** Serves the remote device camera streaming web page. Captures mobile/tablet camera via `getUserMedia`, previews locally, and streams binary JPEG frames over WebSocket to the backend.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
  <title>HTS — Remote Camera</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0f0f1a; --surface: #1a1a2e; --accent: #00c896;
      --text: #e0e0e0; --text-dim: #888; --danger: #e05050; --border: #2a2a45;
    }
    body {
      background: var(--bg); color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      min-height: 100dvh; display: flex; flex-direction: column;
      align-items: center; padding: 20px 16px 32px; gap: 16px;
    }
    header { width: 100%; max-width: 540px; }
    header h1 { font-size: 1.1rem; color: var(--accent); font-weight: 700; }
    header p  { font-size: 0.75rem; color: var(--text-dim); }
    .card {
      width: 100%; max-width: 540px; background: var(--surface);
      border: 1px solid var(--border); border-radius: 14px; padding: 16px;
    }
    #preview-wrap {
      position: relative; width: 100%; aspect-ratio: 16/9;
      background: #0a0a14; border-radius: 10px; overflow: hidden;
    }
    #video { width: 100%; height: 100%; object-fit: cover; display: block; }
    #placeholder {
      position: absolute; inset: 0; display: flex;
      align-items: center; justify-content: center;
      color: var(--text-dim); font-size: 0.85rem; text-align: center; padding: 12px;
    }
    #placeholder.hidden { display: none; }
    #live-badge {
      position: absolute; top: 10px; left: 10px; background: var(--danger);
      color: #fff; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em;
      padding: 3px 8px; border-radius: 4px; display: none;
    }
    #live-badge.visible { display: block; }
    #status-bar { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; padding: 10px 0 4px; }
    #status-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--text-dim); flex-shrink: 0; }
    #status-dot.streaming { background: var(--accent); animation: pulse 1.2s infinite; }
    #status-dot.error { background: var(--danger); }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
    .field-label { font-size: 0.72rem; color: var(--text-dim); margin: 14px 0 5px; }
    #device-name {
      width: 100%; background: #0f0f1a; border: 1px solid var(--border);
      border-radius: 8px; color: var(--text); font-size: 0.88rem; padding: 10px 12px; outline: none;
    }
    #device-name:focus { border-color: var(--accent); }
    .controls { display: flex; gap: 10px; padding-top: 12px; flex-wrap: wrap; }
    button { flex: 1; min-width: 100px; padding: 13px 16px; border: none; border-radius: 10px; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
    button:disabled { opacity: 0.4; cursor: default; }
    #btn-start { background: var(--accent); color: #000; }
    #btn-stop  { background: var(--danger); color: #fff; display: none; }
    #btn-flip  { background: var(--border); color: var(--text); flex: 0 0 auto; }
    #stats { font-size: 0.72rem; color: var(--text-dim); padding-top: 10px; }
    .info { font-size: 0.72rem; color: var(--text-dim); text-align: center; }
  </style>
</head>
<body>
  <header>
    <h1>HTS Remote Camera</h1>
    <p>Human Tracking System — Device Streamer</p>
  </header>
  <div class="card">
    <div id="preview-wrap">
      <video id="video" autoplay playsinline muted></video>
      <div id="placeholder">📷 Camera preview will appear here</div>
      <div id="live-badge">● LIVE</div>
    </div>
    <div id="status-bar">
      <div id="status-dot"></div>
      <span id="status-text">Enter a name and tap Start Streaming.</span>
    </div>
    <p class="field-label">Device name (shown on laptop)</p>
    <input id="device-name" type="text" maxlength="40" placeholder="e.g. iPhone Rear, Lab Cam 2" />
    <div class="controls">
      <button id="btn-start" onclick="startStreaming()">▶ Start Streaming</button>
      <button id="btn-stop"  onclick="stopStreaming()">■ Stop</button>
      <button id="btn-flip"  onclick="flipCamera()">🔄 Flip</button>
    </div>
    <div id="stats"></div>
  </div>
  <p class="info">No app required. Same Wi-Fi network required.</p>

<script>
  "use strict";

  const WS_URL       = "ws://{{WS_HOST}}:{{WS_PORT}}/ws/device";
  const JPEG_QUALITY = 0.80;
  const TARGET_FPS   = 20;

  let ws = null, stream = null, sending = false;
  let lastSent = 0, framesSent = 0, bytesSent = 0;
  let facingMode = "environment";

  const video       = document.getElementById("video");
  const canvas      = document.createElement("canvas");
  const ctx         = canvas.getContext("2d");
  const statusDot   = document.getElementById("status-dot");
  const statusText  = document.getElementById("status-text");
  const liveBadge   = document.getElementById("live-badge");
  const placeholder = document.getElementById("placeholder");
  const btnStart    = document.getElementById("btn-start");
  const btnStop     = document.getElementById("btn-stop");
  const statsEl     = document.getElementById("stats");

  function setStatus(text, state) {
    statusText.textContent = text;
    statusDot.className = state || "";
  }

  function stopMediaStream() {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    if (video) {
      video.srcObject = null;
    }
  }

  async function openCamera() {
    stopMediaStream();
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: facingMode }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      video.srcObject = stream;
      placeholder.classList.add("hidden");
      await video.play().catch(() => {});
      return true;
    } catch (err) {
      stopMediaStream();
      const errMsg = (err.name === "NotAllowedError" || err.name === "PermissionDeniedError")
        ? "Camera access denied. Please allow camera permissions in your browser settings and try again."
        : "Failed to access camera (" + (err.message || err.name) + "). Ensure your camera is connected and not in use.";
      setStatus(errMsg, "error");
      placeholder.classList.remove("hidden");
      return false;
    }
  }

  async function startStreaming() {
    btnStart.disabled = true;
    setStatus("Requesting camera access…", "");

    const success = await openCamera();
    if (!success) {
      btnStart.disabled = false;
      btnStart.style.display = "";
      btnStop.style.display  = "none";
      return;
    }

    setStatus("Connecting to backend…", "");
    try {
      ws = new WebSocket(WS_URL);
      ws.binaryType = "arraybuffer";
    } catch (err) {
      setStatus("Failed to connect to server: " + err.message, "error");
      stopMediaStream();
      btnStart.disabled = false;
      btnStart.style.display = "";
      btnStop.style.display  = "none";
      return;
    }

    ws.onopen = () => {
      const name = document.getElementById("device-name").value.trim()
                   || "Device " + Math.floor(Math.random() * 9000 + 1000);
      ws.send(JSON.stringify({ type: "init", name }));
      setStatus("Streaming to laptop", "streaming");
      liveBadge.classList.add("visible");
      btnStart.style.display = "none";
      btnStop.style.display  = "";
      btnStart.disabled = false;
      sending = true;
      requestAnimationFrame(sendFrame);
    };

    ws.onclose = () => {
      setStatus("Disconnected. Tap Start Streaming to reconnect.", "");
      liveBadge.classList.remove("visible");
      sending = false;
      btnStart.style.display = "";
      btnStop.style.display  = "none";
      btnStart.disabled = false;
    };

    ws.onerror = () => {
      setStatus("Connection error. Is the laptop backend running?", "error");
      btnStart.disabled = false;
    };
  }

  function stopStreaming() {
    sending = false;
    if (ws) {
      ws.close();
      ws = null;
    }
    stopMediaStream();
    placeholder.classList.remove("hidden");
    liveBadge.classList.remove("visible");
    btnStart.style.display = "";
    btnStop.style.display  = "none";
    btnStart.disabled = false;
    setStatus("Stopped.", "");
  }

  async function flipCamera() {
    facingMode = facingMode === "environment" ? "user" : "environment";
    if (stream) {
      await openCamera();
    }
  }

  function sendFrame(ts) {
    if (!sending) return;
    if (ts - lastSent < 1000 / TARGET_FPS) { requestAnimationFrame(sendFrame); return; }
    lastSent = ts;
    const w = video.videoWidth, h = video.videoHeight;
    if (!w || !h) { requestAnimationFrame(sendFrame); return; }
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    ctx.drawImage(video, 0, 0, w, h);
    canvas.toBlob(blob => {
      if (!blob || !ws || ws.readyState !== WebSocket.OPEN) return;
      blob.arrayBuffer().then(buf => {
        ws.send(buf);
        framesSent++;
        bytesSent += buf.byteLength;
        statsEl.textContent = `${framesSent} frames · ${(bytesSent/1024).toFixed(0)} KB`;
      });
    }, "image/jpeg", JPEG_QUALITY);
    requestAnimationFrame(sendFrame);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) sending = false;
    else if (ws?.readyState === WebSocket.OPEN) { sending = true; requestAnimationFrame(sendFrame); }
  });
</script>
</body>
</html>
```

#### Line-by-Line Explanation
- **`stopMediaStream()`**: Iterates `stream.getTracks()` and executes `.stop()` on each track. Sets `video.srcObject = null` to release hardware cleanly.
- **`openCamera()`**: Triggers `navigator.mediaDevices.getUserMedia({ video: ... })` inside a `try/catch` block. On rejection (`NotAllowedError`), invokes `stopMediaStream()` and updates status UI without crashing or setting a persistent error state.
- **`startStreaming()`**: Invoked on user button click. First calls `openCamera()`. If permission succeeds, establishes WebSocket `ws = new WebSocket(WS_URL)` and sets up frame transmission.
- **`stopStreaming()`**: Halts transmission loop, closes WebSocket, calls `stopMediaStream()`, and restores UI buttons to initial state.
- **`flipCamera()`**: Toggles `facingMode` between `"environment"` and `"user"` and re-requests media stream if active.

#### Why Written
Ensures camera permissions are strictly on-demand per W3C standards, allows users to recover from permission denial without refreshing, and prevents browser camera hardware leaks when stopped.

#### How It Connects
Communicates over WebSocket (`WS /ws/device`) sending binary JPEG frames to `backend/transport/ws_receiver.py`.

---

### Modified File 2: `backend/camera/local.py`

**Purpose:** Implements hardware capture for local USB/built-in webcams via OpenCV.

```python
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
            time.sleep(0.5)

            if not cap.isOpened():
                cap.release()
                continue

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
            self._fps                  = fps if fps > 0 else 0.0
            self._is_open              = True
            self._cam_index            = idx
            self._consecutive_failures = 0
            print(f"[LocalCamera] Opened index {idx}: {w}x{h} @ {self._fps:.1f} FPS")
            return True

        print("[LocalCamera] No working camera found at any candidate index.")
        return False

    def read(self) -> tuple[bool, object]:
        if not self._is_open or self._cap is None:
            return False, None

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
```

#### Line-by-Line Explanation
- **`ok, test_frame = cap.read()` in `open()`**: Reads a test frame during candidate scanning. If a device opens but yields no frames, it is safely skipped.
- **`self._consecutive_failures`**: Counter tracking failed `read()` attempts.
- **`if self._consecutive_failures < 10: return False, None`**: Returns non-fatal `(False, None)` on transient dropped frames. `feed.py` sleeps 10ms and retries without dropping the camera from `DeviceRegistry`.
- **`return False, b""`**: Executed only after 10 consecutive failures, signaling a permanent camera hardware disconnect.

#### Why Written
Prevents transient frame drop glitches from destroying the local camera handle and breaking the main UI stream.

#### How It Connects
Called by `feed.py` broadcaster loop via `run_in_executor(None, active.read)`.

---

### Modified File 3: `frontend/src/App.jsx`

**Purpose:** Root React application component. Manages primary layout and lifts the WebSocket feed connection.

```jsx
import { useState } from 'react';
import CameraFeed  from './components/CameraFeed';
import DevicePanel from './components/DevicePanel';
import StatusBar   from './components/StatusBar';
import { useCameraFeed } from './hooks/useCameraFeed';
import './App.css';

export default function App() {
  const [deviceCount, setDeviceCount] = useState(0);
  const feed = useCameraFeed();

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-brand">
          <span className="brand-dot" />
          <h1>Human Tracking System</h1>
        </div>
        <StatusBar connected={feed.connected} deviceCount={deviceCount} />
      </header>
      <main className="app-main">
        <CameraFeed feed={feed} />
        <DevicePanel onDeviceCountChange={setDeviceCount} />
      </main>
    </div>
  );
}
```

#### Line-by-Line Explanation
- **`const feed = useCameraFeed()`**: Instantiates a single WebSocket connection to `/ws/feed` at the root layout level.
- **`<CameraFeed feed={feed} />`**: Passes the active feed object (`frame`, `fps`, `label`, `connected`) down as a prop.

#### Why Written
Eliminates duplicate WebSocket connections between header and main feed components.

---

### Modified File 4: `frontend/src/components/CameraFeed.jsx`

**Purpose:** Renders the live video stream or placeholder.

```jsx
import { useCameraFeed } from '../hooks/useCameraFeed';

export default function CameraFeed({ feed: propFeed }) {
  const hookFeed = useCameraFeed();
  const { frame, fps, label, connected } = propFeed || hookFeed;

  return (
    <div className="camera-feed">
      {frame ? (
        <>
          <img
            src={`data:image/jpeg;base64,${frame}`}
            alt="Live camera feed"
            className="feed-image"
          />
          <div className="feed-overlay">
            <span className="feed-label">{label}</span>
            <span className="feed-fps">{fps} FPS</span>
          </div>
        </>
      ) : (
        <div className="feed-placeholder">
          {connected ? (
            <>
              <span className="placeholder-icon">📷</span>
              <p>No camera active</p>
              <p className="placeholder-hint">Select a device from the panel →</p>
            </>
          ) : (
            <>
              <span className="placeholder-icon">⏳</span>
              <p>Connecting to backend…</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
```

#### Line-by-Line Explanation
- **`const { frame, fps, label, connected } = propFeed || hookFeed`**: Accepts prop feed passed from `App.jsx`, falling back to local hook call if rendered standalone.

---

### Modified File 5: `frontend/src/components/DevicePanel.jsx`

**Purpose:** Renders device list, remote URL link, and active/disconnect action buttons.

```jsx
import { useState, useEffect } from 'react';
import { getDevices, setActiveDevice, disconnectDevice, getStreamerPageUrl } from '../services/api';

export default function DevicePanel({ onDeviceCountChange }) {
  const [devices,     setDevices]     = useState([]);
  const [loading,     setLoading]     = useState(false);
  const [streamerUrl]                 = useState(getStreamerPageUrl);

  useEffect(() => {
    let active = true;

    async function fetchDevices() {
      try {
        const data = await getDevices();
        if (active) {
          setDevices(data);
          onDeviceCountChange?.(data.length);
        }
      } catch {
        // backend not ready, retry on next poll
      }
    }

    fetchDevices();
    const id = setInterval(fetchDevices, 2000);
    return () => { active = false; clearInterval(id); };
  }, [onDeviceCountChange]);

  async function handleSetActive(deviceId) {
    setLoading(true);
    try {
      await setActiveDevice(deviceId);
      const data = await getDevices();
      setDevices(data);
      onDeviceCountChange?.(data.length);
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function handleDisconnect(deviceId) {
    setLoading(true);
    try {
      await disconnectDevice(deviceId);
      const data = await getDevices();
      setDevices(data);
      onDeviceCountChange?.(data.length);
    } catch { /* ignore */ }
    setLoading(false);
  }

  return (
    <div className="device-panel">
      <h2>Device Manager</h2>

      <div className="remote-url-box">
        <p className="remote-url-label">Connect a remote device:</p>
        <p className="remote-url-hint">Open this URL in any browser on the same network:</p>
        <a href={streamerUrl} target="_blank" rel="noreferrer" className="remote-url-link">
          {window.location.hostname}:8000/api/streamer
        </a>
        <p className="remote-url-hint">Or check the backend terminal for the exact LAN URL.</p>
      </div>

      <div className="devices-section">
        <h3>Connected Devices</h3>
        {devices.length === 0 ? (
          <p className="no-devices">No cameras connected.</p>
        ) : (
          <ul className="device-list">
            {devices.map(dev => (
              <li key={dev.id} className={`device-item ${dev.is_active ? 'active' : ''}`}>
                <div className="device-info">
                  <span className={`device-status-dot ${dev.is_open ? 'open' : 'closed'}`} />
                  <div>
                    <p className="device-label">{dev.label}</p>
                    <p className="device-meta">
                      {dev.width > 0 ? `${dev.width}×${dev.height}` : 'Waiting for stream…'}
                      {dev.is_active && ' · ACTIVE'}
                    </p>
                  </div>
                </div>
                <div className="device-actions">
                  {!dev.is_active && (
                    <button className="btn-view" onClick={() => handleSetActive(dev.id)} disabled={loading}>
                      View
                    </button>
                  )}
                  <button className="btn-disconnect" onClick={() => handleDisconnect(dev.id)} disabled={loading}>
                    Disconnect
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
```

#### Line-by-Line Explanation
- **`handleSetActive` & `handleDisconnect`**: Immediately invoke `getDevices()` following API POST requests to update UI device lists and active highlights without waiting for the 2-second poll.

---

## Fix 3 — Remote Camera Streamer HTTPS & Secure Context Fix

### Detailed Technical Rationale & Root Cause Analysis

#### 1. Why `navigator.mediaDevices` was `undefined`
Modern web browsers enforce strict security boundaries around hardware access via the **W3C Secure Contexts specification**. Under this standard, sensitive APIs — including `navigator.mediaDevices` and `navigator.mediaDevices.getUserMedia` — are strictly stripped from the `navigator` object in non-secure contexts. When a browser loads a web page over plain unencrypted HTTP on a network IP, `window.isSecureContext` is `false`. Because `navigator.mediaDevices` is omitted entirely, evaluating `navigator.mediaDevices.getUserMedia` attempts to read property `.getUserMedia` on `undefined`, triggering a fatal JavaScript `TypeError: undefined is not an object (evaluating 'navigator.mediaDevices.getUserMedia')`.

#### 2. Why HTTP using a LAN IP failed on the iPhone
When accessing `http://192.168.1.23:8000/api/streamer` from an iPhone (iOS Safari or Chrome), the browser resolves the connection over plain HTTP to a private local area network (LAN) IP address. Because unencrypted network IP origins can be snooped or tampered with on public/shared Wi-Fi networks, mobile browsers treat `http://192.168.1.x` as an insecure origin (`window.isSecureContext === false`). As a result, Safari and Chrome for iOS disable `navigator.mediaDevices` completely over HTTP LAN addresses.

#### 3. What a Secure Context is
A **Secure Context** is a document or worker context in which the browser has verified that the web page was delivered over an authenticated, encrypted protocol (HTTPS/TLS) or loaded from a trusted local loopback address. In a Secure Context (`window.isSecureContext === true`), the browser enables high-privilege device APIs such as webcams, microphones, geolocation, Web Bluetooth, and cryptography because the origin guarantees data confidentiality, origin authenticity, and message integrity.

#### 4. Why `localhost` behaves differently from a LAN IP
Web standard specifications explicitly carve out an exception for local loopback addresses (`localhost` and `127.0.0.1`). Browsers consider connections to `localhost` to be inherently internal to the device, so data does not cross physical network interfaces. Consequently, browsers classify `http://localhost` as a Secure Context (`window.isSecureContext === true`), allowing camera access over unencrypted HTTP during local desktop development. In contrast, LAN IP addresses (e.g. `192.168.1.23`) cross physical network interfaces (Wi-Fi/Ethernet) and are not exempt, strictly requiring HTTPS.

---

## Flow 4 — Secure Context HTTPS Remote Streamer Architecture & Flow Diagram

```
User opens remote streamer URL on iPhone (https://192.168.1.23:8000/api/streamer)
        │
        ▼
TLS/SSL handshake over HTTPS (Self-signed certificate)
        │
        ▼
iOS Safari displays "Connection Not Private" warning
        │
        ▼
User taps "Advanced" → "Proceed to 192.168.1.23 (unsafe)"
        │
        ▼
Streamer HTML loads with window.isSecureContext === true
        │
        ▼
Explicit safety checks run:
  1. window.isSecureContext verified (true)
  2. navigator.mediaDevices verified (defined)
  3. navigator.mediaDevices.getUserMedia verified (function exists)
        │
        ▼
User taps "▶ Start Streaming" button
        │
        ▼
navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
        │
        ▼
iOS Safari shows native camera permission dialog ("Allow site to use camera?")
        ├──► ALLOW:
        │      │
        │      ▼
        │    MediaStream assigned to <video> element → live preview renders
        │      │
        │      ▼
        │    WebSocket connection opened over wss://192.168.1.23:8000/ws/device
        │      │
        │      ▼
        │    Init payload sent: {"type": "init", "name": "iPhone Rear"}
        │      │
        │      ▼
        │    Frames captured to <canvas>, compressed to JPEG (quality 0.80),
        │    and transmitted as binary ArrayBuffers over wss:// at 20 FPS
        │      │
        │      ▼
        │    FastAPI ws_receiver decodes JPEG to BGR numpy array
        │    and pushes frame into RemoteCamera instance
        │      │
        │      ▼
        │    React frontend displays live phone camera feed on laptop screen
        │
        └──► DENY / INSECURE CONTEXT:
               │
               ▼
             Clear error displayed in UI status bar:
             "Camera access requires a secure context (HTTPS)..."
             No undefined functions called, button remains enabled for retry
```

---

## Complete Code & Explanations for HTTPS Fix

### File 1: `backend/certs.py` — **NEW**

**Purpose:** Programmatically generates a self-signed X.509 certificate (`cert.pem`) and private key (`key.pem`) for local development using Python's `cryptography` library.

#### Complete Code

```python
from __future__ import annotations
import datetime
import ipaddress
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DEFAULT_CERT_FILE = _PROJECT_ROOT / "cert.pem"
DEFAULT_KEY_FILE  = _PROJECT_ROOT / "key.pem"


def ensure_certificates(
    cert_path: Path | str = DEFAULT_CERT_FILE,
    key_path:  Path | str = DEFAULT_KEY_FILE,
    local_ip:  str | None = None,
) -> tuple[str, str]:
    cert_p = Path(cert_path)
    key_p  = Path(key_path)

    if cert_p.exists() and key_p.exists():
        return str(cert_p), str(key_p)

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject_ip = local_ip or "localhost"
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, subject_ip),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HTS Local Dev"),
    ])

    alt_names: list[x509.GeneralName] = [
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]

    if local_ip and local_ip != "127.0.0.1":
        try:
            alt_names.append(x509.IPAddress(ipaddress.ip_address(local_ip)))
        except ValueError:
            alt_names.append(x509.DNSName(local_ip))

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(alt_names),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    key_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cert_bytes = cert.public_bytes(serialization.Encoding.PEM)

    key_p.write_bytes(key_bytes)
    cert_p.write_bytes(cert_bytes)

    print(f"[Cert] Generated self-signed dev certificate:\n  Cert: {cert_p}\n  Key:  {key_p}")
    return str(cert_p), str(key_p)


if __name__ == "__main__":
    ensure_certificates()
```

#### Line-by-Line Explanation

- **`rsa.generate_private_key(public_exponent=65537, key_size=2048)`**: Generates a 2048-bit RSA private key using standard RSA exponent 65537.
- **`x509.SubjectAlternativeName(...)`**: Embeds Subject Alternative Names (SAN) for `localhost`, `127.0.0.1`, and the machine's detected LAN IP address. Without SAN extensions matching the target IP, modern mobile browsers reject SSL certificates.
- **`x509.CertificateBuilder()`**: Constructs a self-signed X.509 v3 certificate valid for 365 days signed using SHA-256.
- **`key_p.write_bytes(key_bytes)` / `cert_p.write_bytes(cert_bytes)`**: Writes `key.pem` and `cert.pem` to the project root directory.

#### Why Written
Enables standard, zero-dependency SSL certificate generation for local HTTPS development without needing third-party binaries or external tools.

---

### File 2: `backend/config.py` — **MODIFIED**

**Purpose:** Defines central system constants including HTTPS protocol flags and full streamer URLs.

#### Complete Code

```python
import socket


def _get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


BACKEND_PORT: int = 8000
CAMERA_INDEX_CANDIDATES: list[int] = [0, 1, 2, 3, 4]
MAX_FRAME_QUEUE: int = 5
REMOTE_READ_TIMEOUT: float = 0.05
FEED_JPEG_QUALITY: int = 80
LOCAL_IP: str = _get_local_ip()
HTTPS_ENABLED: bool = True
STREAMER_URL: str = f"https://{LOCAL_IP}:{BACKEND_PORT}/api/streamer"
```

#### Line-by-Line Explanation

- **`HTTPS_ENABLED = True`**: Central flag designating HTTPS as the active protocol.
- **`STREAMER_URL = f"https://{LOCAL_IP}:{BACKEND_PORT}/api/streamer"`**: Constructs the full HTTPS LAN URL used by startup banners and REST endpoints.

---

### File 3: `backend/main.py` — **MODIFIED**

**Purpose:** FastAPI application entrypoint with updated startup logs and Uvicorn SSL server launcher.

#### Complete Code

```python
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import backend.config as config
from backend.api import feed, routes
from backend.camera.local import LocalCamera
from backend.devices.registry import registry
from backend.transport import ws_receiver


@asynccontextmanager
async def lifespan(app: FastAPI):
    local_cam = LocalCamera()
    if local_cam.open():
        registry.add(local_cam)
    else:
        print(
            "[HTS] WARNING: No local camera found.\n"
            "      Running in remote-only mode."
        )

    broadcaster_task = asyncio.create_task(feed.start_broadcaster())

    print("\n" + "=" * 56)
    print("  HTS — Multi-Device Camera Backend")
    print("=" * 56)
    print(f"  Backend API:      https://localhost:{config.BACKEND_PORT}")
    print(f"  Remote streamer:  {config.STREAMER_URL}")
    print(f"  Open React UI:    http://localhost:5173")
    print("=" * 56 + "\n")

    yield

    broadcaster_task.cancel()
    try:
        await broadcaster_task
    except asyncio.CancelledError:
        pass
    registry.release_all()
    print("[HTS] Backend shut down cleanly.")


app = FastAPI(title="HTS Backend", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router,      prefix="/api")
app.include_router(feed.router)
app.include_router(ws_receiver.router)


if __name__ == "__main__":
    import uvicorn
    from backend.certs import ensure_certificates
    cert_file, key_file = ensure_certificates(local_ip=config.LOCAL_IP)
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=config.BACKEND_PORT,
        ssl_certfile=cert_file,
        ssl_keyfile=key_file,
        reload=False,
    )
```

#### Line-by-Line Explanation

- **`ensure_certificates(local_ip=config.LOCAL_IP)`**: Automatically generates `cert.pem` and `key.pem` before launching Uvicorn if certificates do not exist.
- **`ssl_certfile=cert_file, ssl_keyfile=key_file`**: Instructs Uvicorn to run with SSL encryption enabled on port 8000.

---

### File 4: `backend/api/routes.py` — **MODIFIED**

**Purpose:** Exposes REST endpoints for devices and backend system metadata.

#### Complete Code

```python
from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import backend.config as config
from backend.devices.registry import registry
from backend.transport import ws_receiver

router = APIRouter()

_STREAMER_PATH = (
    Path(__file__).parent.parent / "transport" / "static" / "streamer.html"
)


@router.get("/info")
def get_info() -> dict:
    return {
        "streamer_url": config.STREAMER_URL,
        "local_ip":     config.LOCAL_IP,
        "port":         config.BACKEND_PORT,
        "protocol":     "https",
    }


@router.get("/devices")
def get_devices() -> list[dict]:
    return [
        {
            "id":        device_id,
            "label":     cam.label,
            "width":     cam.width,
            "height":    cam.height,
            "is_open":   cam.is_open,
            "is_active": is_active,
        }
        for device_id, cam, is_active in registry.list_devices()
    ]


@router.post("/devices/{device_id}/active")
def set_active_device(device_id: str) -> dict:
    if not registry.set_active(device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "ok", "active": device_id}


@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(device_id: str) -> dict:
    await ws_receiver.close_device(device_id)
    registry.remove(device_id)
    return {"status": "ok"}


@router.get("/streamer", response_class=HTMLResponse)
def serve_streamer() -> HTMLResponse:
    try:
        html = _STREAMER_PATH.read_text(encoding="utf-8")
    except OSError:
        raise HTTPException(status_code=500, detail="streamer.html not found")
    html = html.replace("{{WS_HOST}}", config.LOCAL_IP)
    html = html.replace("{{WS_PORT}}", str(config.BACKEND_PORT))
    return HTMLResponse(content=html)
```

#### Line-by-Line Explanation

- **`@router.get("/info")`**: Returns backend metadata payload containing `streamer_url` (`https://<LAN_IP>:8000/api/streamer`), allowing frontend components to render exact reachable HTTPS streamer links dynamically.

---

### File 5: `backend/transport/static/streamer.html` — **MODIFIED**

**Purpose:** Mobile browser streamer page with explicit Secure Context validation, robust error handling, and dynamic `wss://` WebSocket support.

#### Complete Code

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
  <title>HTS — Remote Camera</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0f0f1a; --surface: #1a1a2e; --accent: #00c896;
      --text: #e0e0e0; --text-dim: #888; --danger: #e05050; --border: #2a2a45;
    }
    body {
      background: var(--bg); color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      min-height: 100dvh; display: flex; flex-direction: column;
      align-items: center; padding: 20px 16px 32px; gap: 16px;
    }
    header { width: 100%; max-width: 540px; }
    header h1 { font-size: 1.1rem; color: var(--accent); font-weight: 700; }
    header p  { font-size: 0.75rem; color: var(--text-dim); }
    .card {
      width: 100%; max-width: 540px; background: var(--surface);
      border: 1px solid var(--border); border-radius: 14px; padding: 16px;
    }
    #preview-wrap {
      position: relative; width: 100%; aspect-ratio: 16/9;
      background: #0a0a14; border-radius: 10px; overflow: hidden;
    }
    #video { width: 100%; height: 100%; object-fit: cover; display: block; }
    #placeholder {
      position: absolute; inset: 0; display: flex;
      align-items: center; justify-content: center;
      color: var(--text-dim); font-size: 0.85rem; text-align: center; padding: 12px;
    }
    #placeholder.hidden { display: none; }
    #live-badge {
      position: absolute; top: 10px; left: 10px; background: var(--danger);
      color: #fff; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em;
      padding: 3px 8px; border-radius: 4px; display: none;
    }
    #live-badge.visible { display: block; }
    #status-bar { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; padding: 10px 0 4px; }
    #status-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--text-dim); flex-shrink: 0; }
    #status-dot.streaming { background: var(--accent); animation: pulse 1.2s infinite; }
    #status-dot.error { background: var(--danger); }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
    .field-label { font-size: 0.72rem; color: var(--text-dim); margin: 14px 0 5px; }
    #device-name {
      width: 100%; background: #0f0f1a; border: 1px solid var(--border);
      border-radius: 8px; color: var(--text); font-size: 0.88rem; padding: 10px 12px; outline: none;
    }
    #device-name:focus { border-color: var(--accent); }
    .controls { display: flex; gap: 10px; padding-top: 12px; flex-wrap: wrap; }
    button { flex: 1; min-width: 100px; padding: 13px 16px; border: none; border-radius: 10px; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
    button:disabled { opacity: 0.4; cursor: default; }
    #btn-start { background: var(--accent); color: #000; }
    #btn-stop  { background: var(--danger); color: #fff; display: none; }
    #btn-flip  { background: var(--border); color: var(--text); flex: 0 0 auto; }
    #stats { font-size: 0.72rem; color: var(--text-dim); padding-top: 10px; }
    .info { font-size: 0.72rem; color: var(--text-dim); text-align: center; }
  </style>
</head>
<body>
  <header>
    <h1>HTS Remote Camera</h1>
    <p>Human Tracking System — Device Streamer</p>
  </header>
  <div class="card">
    <div id="preview-wrap">
      <video id="video" autoplay playsinline muted></video>
      <div id="placeholder">📷 Camera preview will appear here</div>
      <div id="live-badge">● LIVE</div>
    </div>
    <div id="status-bar">
      <div id="status-dot"></div>
      <span id="status-text">Enter a name and tap Start Streaming.</span>
    </div>
    <p class="field-label">Device name (shown on laptop)</p>
    <input id="device-name" type="text" maxlength="40" placeholder="e.g. iPhone Rear, Lab Cam 2" />
    <div class="controls">
      <button id="btn-start" onclick="startStreaming()">▶ Start Streaming</button>
      <button id="btn-stop"  onclick="stopStreaming()">■ Stop</button>
      <button id="btn-flip"  onclick="flipCamera()">🔄 Flip</button>
    </div>
    <div id="stats"></div>
  </div>
  <p class="info">No app required. Same Wi-Fi network required.</p>

<script>
  "use strict";

  const wsProtocol   = window.location.protocol === "https:" ? "wss:" : "ws:";
  const WS_URL       = `${wsProtocol}//${window.location.host}/ws/device`;
  const JPEG_QUALITY = 0.80;
  const TARGET_FPS   = 20;

  let ws = null, stream = null, sending = false;
  let lastSent = 0, framesSent = 0, bytesSent = 0;
  let facingMode = "environment";

  const video       = document.getElementById("video");
  const canvas      = document.createElement("canvas");
  const ctx         = canvas.getContext("2d");
  const statusDot   = document.getElementById("status-dot");
  const statusText  = document.getElementById("status-text");
  const liveBadge   = document.getElementById("live-badge");
  const placeholder = document.getElementById("placeholder");
  const btnStart    = document.getElementById("btn-start");
  const btnStop     = document.getElementById("btn-stop");
  const statsEl     = document.getElementById("stats");

  function setStatus(text, state) {
    statusText.textContent = text;
    statusDot.className = state || "";
  }

  function stopMediaStream() {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    if (video) {
      video.srcObject = null;
    }
  }

  async function openCamera() {
    stopMediaStream();

    if (!window.isSecureContext) {
      setStatus("Camera access requires a secure context (HTTPS). Please open this page using https:// (e.g. https://" + window.location.host + "/api/streamer).", "error");
      placeholder.classList.remove("hidden");
      return false;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("Browser camera API (navigator.mediaDevices.getUserMedia) is unavailable. Ensure you are using HTTPS.", "error");
      placeholder.classList.remove("hidden");
      return false;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: facingMode }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      video.srcObject = stream;
      placeholder.classList.add("hidden");
      await video.play().catch(() => {});
      return true;
    } catch (err) {
      stopMediaStream();
      const errMsg = (err.name === "NotAllowedError" || err.name === "PermissionDeniedError")
        ? "Camera access denied. Please allow camera permissions in your browser settings and try again."
        : "Failed to access camera (" + (err.message || err.name) + "). Ensure your camera is connected and not in use.";
      setStatus(errMsg, "error");
      placeholder.classList.remove("hidden");
      return false;
    }
  }

  async function startStreaming() {
    btnStart.disabled = true;
    setStatus("Requesting camera access…", "");

    const success = await openCamera();
    if (!success) {
      btnStart.disabled = false;
      btnStart.style.display = "";
      btnStop.style.display  = "none";
      return;
    }

    setStatus("Connecting to backend…", "");
    try {
      ws = new WebSocket(WS_URL);
      ws.binaryType = "arraybuffer";
    } catch (err) {
      setStatus("Failed to connect to server: " + err.message, "error");
      stopMediaStream();
      btnStart.disabled = false;
      btnStart.style.display = "";
      btnStop.style.display  = "none";
      return;
    }

    ws.onopen = () => {
      const name = document.getElementById("device-name").value.trim()
                   || "Device " + Math.floor(Math.random() * 9000 + 1000);
      ws.send(JSON.stringify({ type: "init", name }));
      setStatus("Streaming to laptop", "streaming");
      liveBadge.classList.add("visible");
      btnStart.style.display = "none";
      btnStop.style.display  = "";
      btnStart.disabled = false;
      sending = true;
      requestAnimationFrame(sendFrame);
    };

    ws.onclose = () => {
      setStatus("Disconnected. Tap Start Streaming to reconnect.", "");
      liveBadge.classList.remove("visible");
      sending = false;
      btnStart.style.display = "";
      btnStop.style.display  = "none";
      btnStart.disabled = false;
    };

    ws.onerror = () => {
      setStatus("Connection error. Is the laptop backend running?", "error");
      btnStart.disabled = false;
    };
  }

  function stopStreaming() {
    sending = false;
    if (ws) {
      ws.close();
      ws = null;
    }
    stopMediaStream();
    placeholder.classList.remove("hidden");
    liveBadge.classList.remove("visible");
    btnStart.style.display = "";
    btnStop.style.display  = "none";
    btnStart.disabled = false;
    setStatus("Stopped.", "");
  }

  async function flipCamera() {
    facingMode = facingMode === "environment" ? "user" : "environment";
    if (stream) {
      await openCamera();
    }
  }

  function sendFrame(ts) {
    if (!sending) return;
    if (ts - lastSent < 1000 / TARGET_FPS) { requestAnimationFrame(sendFrame); return; }
    lastSent = ts;
    const w = video.videoWidth, h = video.videoHeight;
    if (!w || !h) { requestAnimationFrame(sendFrame); return; }
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    ctx.drawImage(video, 0, 0, w, h);
    canvas.toBlob(blob => {
      if (!blob || !ws || ws.readyState !== WebSocket.OPEN) return;
      blob.arrayBuffer().then(buf => {
        ws.send(buf);
        framesSent++;
        bytesSent += buf.byteLength;
        statsEl.textContent = `${framesSent} frames · ${(bytesSent/1024).toFixed(0)} KB`;
      });
    }, "image/jpeg", JPEG_QUALITY);
    requestAnimationFrame(sendFrame);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) sending = false;
    else if (ws?.readyState === WebSocket.OPEN) { sending = true; requestAnimationFrame(sendFrame); }
  });
</script>
</body>
</html>
```

#### Line-by-Line Explanation

- **`const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"`**: Dynamically determines WebSocket protocol (`wss:` when HTTPS, `ws:` when HTTP), avoiding mixed-content security errors.
- **`if (!window.isSecureContext)`**: Explicit safety check verifying browser Secure Context state before attempting camera access.
- **`if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia)`**: Explicit check guarding against calling `undefined` functions.

---

### File 6: `frontend/vite.config.js` — **MODIFIED**

**Purpose:** Vite development server proxy configuration supporting HTTPS backend targets and self-signed certificates.

#### Complete Code

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'wss://localhost:8000',
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
```

#### Line-by-Line Explanation

- **`target: 'https://localhost:8000'` & `target: 'wss://localhost:8000'`**: Routes Vite dev proxy targets to backend HTTPS and WebSocket ports.
- **`secure: false`**: Configures Node HTTP/WS proxy to accept self-signed development certificates without throwing TLS verification errors.

---

### File 7: `frontend/src/services/api.js` — **MODIFIED**

**Purpose:** Frontend API service helper functions.

#### Complete Code

```javascript
export async function getDevices() {
  const res = await fetch('/api/devices');
  if (!res.ok) throw new Error(`GET /api/devices failed: ${res.status}`);
  return res.json();
}

export async function setActiveDevice(deviceId) {
  const res = await fetch(`/api/devices/${deviceId}/active`, { method: 'POST' });
  if (!res.ok) throw new Error(`POST .../active failed: ${res.status}`);
  return res.json();
}

export async function disconnectDevice(deviceId) {
  const res = await fetch(`/api/devices/${deviceId}/disconnect`, { method: 'POST' });
  if (!res.ok) throw new Error(`POST .../disconnect failed: ${res.status}`);
  return res.json();
}

export async function getSystemInfo() {
  const res = await fetch('/api/info');
  if (!res.ok) throw new Error(`GET /api/info failed: ${res.status}`);
  return res.json();
}

export function getStreamerPageUrl() {
  return '/api/streamer';
}
```

#### Line-by-Line Explanation

- **`getSystemInfo()`**: Fetches system metadata from `/api/info` to retrieve the backend's active HTTPS LAN URL.

---

### File 8: `frontend/src/components/DevicePanel.jsx` — **MODIFIED**

**Purpose:** Renders device list and displays exact HTTPS LAN URL for remote devices.

#### Complete Code

```jsx
import { useState, useEffect } from 'react';
import { getDevices, setActiveDevice, disconnectDevice, getSystemInfo } from '../services/api';

export default function DevicePanel({ onDeviceCountChange }) {
  const [devices,     setDevices]     = useState([]);
  const [loading,     setLoading]     = useState(false);
  const [streamerUrl, setStreamerUrl] = useState('');

  useEffect(() => {
    let active = true;

    async function fetchInfo() {
      try {
        const info = await getSystemInfo();
        if (active && info.streamer_url) {
          setStreamerUrl(info.streamer_url);
        }
      } catch {
        // use fallback if backend info not reachable
      }
    }

    async function fetchDevices() {
      try {
        const data = await getDevices();
        if (active) {
          setDevices(data);
          onDeviceCountChange?.(data.length);
        }
      } catch {
        // backend not ready, retry on next poll
      }
    }

    fetchInfo();
    fetchDevices();
    const id = setInterval(fetchDevices, 2000);
    return () => { active = false; clearInterval(id); };
  }, [onDeviceCountChange]);

  async function handleSetActive(deviceId) {
    setLoading(true);
    try {
      await setActiveDevice(deviceId);
      const data = await getDevices();
      setDevices(data);
      onDeviceCountChange?.(data.length);
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function handleDisconnect(deviceId) {
    setLoading(true);
    try {
      await disconnectDevice(deviceId);
      const data = await getDevices();
      setDevices(data);
      onDeviceCountChange?.(data.length);
    } catch { /* ignore */ }
    setLoading(false);
  }

  const displayUrl = streamerUrl || `https://${window.location.hostname}:8000/api/streamer`;

  return (
    <div className="device-panel">
      <h2>Device Manager</h2>

      <div className="remote-url-box">
        <p className="remote-url-label">Connect a remote device:</p>
        <p className="remote-url-hint">Open this URL in any browser on the same network:</p>
        <a href={displayUrl} target="_blank" rel="noreferrer" className="remote-url-link">
          {displayUrl}
        </a>
        <p className="remote-url-hint">Or check the backend terminal for the exact LAN URL.</p>
      </div>

      <div className="devices-section">
        <h3>Connected Devices</h3>
        {devices.length === 0 ? (
          <p className="no-devices">No cameras connected.</p>
        ) : (
          <ul className="device-list">
            {devices.map(dev => (
              <li key={dev.id} className={`device-item ${dev.is_active ? 'active' : ''}`}>
                <div className="device-info">
                  <span className={`device-status-dot ${dev.is_open ? 'open' : 'closed'}`} />
                  <div>
                    <p className="device-label">{dev.label}</p>
                    <p className="device-meta">
                      {dev.width > 0 ? `${dev.width}×${dev.height}` : 'Waiting for stream…'}
                      {dev.is_active && ' · ACTIVE'}
                    </p>
                  </div>
                </div>
                <div className="device-actions">
                  {!dev.is_active && (
                    <button className="btn-view" onClick={() => handleSetActive(dev.id)} disabled={loading}>
                      View
                    </button>
                  )}
                  <button className="btn-disconnect" onClick={() => handleDisconnect(dev.id)} disabled={loading}>
                    Disconnect
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
```

#### Line-by-Line Explanation

- **`displayUrl = streamerUrl || ...`**: Renders the complete HTTPS LAN address (`https://192.168.1.23:8000/api/streamer`) directly in the UI instead of `localhost:8000`.

---

### File 9: `frontend/src/hooks/useCameraFeed.js` — **MODIFIED**

**Purpose:** Custom hook maintaining React's main feed WebSocket connection.

#### Complete Code

```javascript
import { useState, useEffect, useRef } from 'react';

export function useCameraFeed() {
  const [frame,     setFrame]     = useState(null);
  const [fps,       setFps]       = useState(0);
  const [label,     setLabel]     = useState('');
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      if (cancelled) return;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/feed`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!cancelled) setConnected(true);
      };

      ws.onclose = () => {
        if (!cancelled) {
          setConnected(false);
          setFrame(null);
          setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (event) => {
        if (cancelled) return;
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'frame') {
            setFrame(msg.frame);
            setFps(msg.fps);
            setLabel(msg.label);
          } else if (msg.type === 'no_camera') {
            setFrame(null);
            setLabel('');
          }
        } catch {
          // ignore malformed messages
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { frame, fps, label, connected };
}
```

#### Line-by-Line Explanation

- **`const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'`**: Dynamically switches between WebSocket (`ws:`) and Secure WebSocket (`wss:`) based on page origin.

---

## Fix 4 — Multi-Device Active Display & Remote Frame Sync Fix

### Detailed Rationale & Root Cause Analysis

#### 1. What Problem Existed
When a remote phone camera connected to the application, it successfully registered with the backend and appeared in the **Connected Devices** list in the React sidebar (marked as `ACTIVE`). However, the main video display area remained stuck showing `"No camera active"`. Furthermore, clicking the "View" button or switching between cameras failed to render video on the main screen.

#### 2. Why the Device Appeared as Connected But Was Not Displayed
Three underlying issues contributed to this failure across the streaming pipeline:
1. **Unthrottled Broadcaster Loop Overloading WebSocket (`backend/api/feed.py`)**: `feed.py` ran an unthrottled `while True:` loop without frame rate pacing. When `RemoteCamera.read()` returned `(True, _latest_frame)` instantly from memory, `feed.py` encoded and broadcasted thousands of JPEG messages per second over `/ws/feed`. This flooded Vite's proxy and browser WebSocket buffers, causing `[vite] ws proxy error` and disconnecting the browser feed WebSocket. Once disconnected, React's video state reset to `null`, rendering the `"No camera active"` placeholder.
2. **Unusable Camera Fallback Handling (`backend/camera/local.py` & `registry.py`)**: When a laptop camera failed to read frames (e.g. if unavailable or closed), `LocalCamera.read()` returned `(False, None)` indefinitely instead of `(False, b"")` (fatal failure signal). As a result, `registry._active_id` remained stuck on `"local:0"`, and `feed.py` looped forever without broadcasting or auto-switching to the connected remote camera (`Iphone`).
3. **Duplicate Frontend WebSocket Connections (`CameraFeed.jsx`)**: `CameraFeed.jsx` called `useCameraFeed()` internally even though `App.jsx` already passed `feed` as a prop, creating duplicate parallel WebSockets that competed for frame updates.

---

## Flow 5 — Remote Phone Camera to React Main Display Complete Data Flow

```
Phone Camera (<video>)
        │
        ▼
HTML5 Canvas captures JPEG blob (Quality 0.80) at 20 FPS
        │
        ▼
Binary ArrayBuffer transmitted over Secure WebSocket (wss://<IP>:8000/ws/device)
        │
        ▼
FastAPI ws_receiver decodes JPEG byte stream to OpenCV BGR numpy array
        │
        ▼
remote_cam.push_frame(frame) updates thread-safe _latest_frame buffer & _is_open = True
        │
        ▼
User clicks "View" next to Phone Camera in React UI
        │
        ▼
React posts POST /api/devices/{encoded_id}/active -> registry.set_active(id)
        │
        ▼
feed.py broadcaster loop calls active.read() on RemoteCamera instance
        │
        ▼
RemoteCamera.read() returns (True, _latest_frame) in O(1) time under lock
        │
        ▼
feed.py encodes frame to JPEG base64 string, broadcasts over /ws/feed, and sleeps 33ms (30 FPS pacing)
        │
        ▼
useCameraFeed hook in React receives WebSocket message -> updates setFrame(b64)
        │
        ▼
CameraFeed component renders live video image <img src="data:image/jpeg;base64,..."> on main display
```


---

## Complete Code & Explanations for Multi-Device Fix

### File 1: `backend/camera/remote.py` — **MODIFIED**

**Purpose:** Implements thread-safe `_latest_frame` buffer storage for remote camera streams.

#### Complete Code

```python
from __future__ import annotations
import threading
import time
import numpy as np
from backend.camera.base import CameraSource


class RemoteCamera(CameraSource):

    def __init__(self, device_id: str, label: str) -> None:
        self._device_id           = device_id
        self._label               = label
        self._lock                = threading.Lock()
        self._latest_frame:        np.ndarray | None = None
        self._width:               int   = 0
        self._height:              int   = 0
        self._is_open:             bool  = False
        self._last_update_time:    float = 0.0

    def push_frame(self, frame: np.ndarray) -> None:
        with self._lock:
            self._latest_frame     = frame
            self._height, self._width = frame.shape[:2]
            self._is_open          = True
            self._last_update_time = time.time()

    def mark_disconnected(self) -> None:
        with self._lock:
            self._is_open = False
            self._latest_frame = None

    def open(self) -> bool:
        with self._lock:
            self._is_open = True
        return True

    def read(self) -> tuple[bool, object]:
        with self._lock:
            if not self._is_open or self._latest_frame is None:
                return False, None

            if time.time() - self._last_update_time > 5.0:
                self._is_open = False
                return False, b""

            return True, self._latest_frame

    def release(self) -> None:
        with self._lock:
            self._is_open = False
            self._latest_frame = None
        print(f"[RemoteCamera] Released: {self._label}")

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
```

#### Line-by-Line Explanation

- **`self._lock = threading.Lock()`**: Initializes a thread lock to synchronize frame updates between the WebSocket receiver thread (`ws_receiver.py`) and the broadcaster loop (`feed.py`).
- **`push_frame(self, frame)`**: Stores the incoming NumPy frame in `_latest_frame`, extracts pixel dimensions (`_width`, `_height`), sets `_is_open = True`, and updates `_last_update_time`.
- **`read(self)`**: Reads `_latest_frame` under lock protection. If `_latest_frame` is present, it returns `(True, _latest_frame)` in O(1) time without blocking. If no new frames have arrived for over 5 seconds, it marks the device as disconnected and returns `(False, b"")`.

#### Why Necessary
Eliminates frame queue exhaustion glitches, guaranteeing that `feed.py` always receives the most recent valid video frame for continuous broadcasting.

---

### File 2: `backend/devices/registry.py` — **MODIFIED**

**Purpose:** Thread-safe device registry with automatic active device fallback resolution.

#### Complete Code

```python
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
            self._devices[cam.device_id] = cam
            if self._active_id is None or self._active_id not in self._devices:
                self._active_id = cam.device_id

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

    def set_active(self, device_id: str) -> bool:
        with self._lock:
            if device_id not in self._devices:
                return False
            self._active_id = device_id
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
            return self._devices.get(self._active_id)

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
```

#### Line-by-Line Explanation

- **`get_active(self)`**: Checks if `_active_id` is `None` or points to a device no longer in `_devices`. If so, it automatically assigns `_active_id` to `next(iter(self._devices), None)`, ensuring that as long as any camera is connected, an active device is selected.
- **`add(self, cam)`**: Auto-activates newly added devices if no active device is currently set.

#### Why Necessary
Prevents the system from getting stuck in a "No camera active" state when cameras are added, removed, or switched.

---

### File 3: `frontend/src/services/api.js` — **MODIFIED**

**Purpose:** API service helper module for REST requests.

#### Complete Code

```javascript
export async function getDevices() {
  const res = await fetch('/api/devices');
  if (!res.ok) throw new Error(`GET /api/devices failed: ${res.status}`);
  return res.json();
}

export async function setActiveDevice(deviceId) {
  const res = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/active`, { method: 'POST' });
  if (!res.ok) throw new Error(`POST .../active failed: ${res.status}`);
  return res.json();
}

export async function disconnectDevice(deviceId) {
  const res = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/disconnect`, { method: 'POST' });
  if (!res.ok) throw new Error(`POST .../disconnect failed: ${res.status}`);
  return res.json();
}

export async function getSystemInfo() {
  const res = await fetch('/api/info');
  if (!res.ok) throw new Error(`GET /api/info failed: ${res.status}`);
  return res.json();
}

export function getStreamerPageUrl() {
  return '/api/streamer';
}
```

#### Line-by-Line Explanation

- **`encodeURIComponent(deviceId)`**: Encodes special characters in device ID path parameters (such as `local:0`), ensuring clean HTTP request routing.

---

### File 4: `frontend/src/components/DevicePanel.jsx` — **MODIFIED**

**Purpose:** Renders the Connected Devices sidebar and active device controls.

#### Complete Code

```jsx
import { useState, useEffect } from 'react';
import { getDevices, setActiveDevice, disconnectDevice, getSystemInfo } from '../services/api';

export default function DevicePanel({ onDeviceCountChange }) {
  const [devices,     setDevices]     = useState([]);
  const [loading,     setLoading]     = useState(false);
  const [streamerUrl, setStreamerUrl] = useState('');

  useEffect(() => {
    let active = true;

    async function fetchInfo() {
      try {
        const info = await getSystemInfo();
        if (active && info.streamer_url) {
          setStreamerUrl(info.streamer_url);
        }
      } catch {}
    }

    async function fetchDevices() {
      try {
        const data = await getDevices();
        if (active) {
          setDevices(data);
          onDeviceCountChange?.(data.length);
        }
      } catch {}
    }

    fetchInfo();
    fetchDevices();
    const id = setInterval(fetchDevices, 2000);
    return () => { active = false; clearInterval(id); };
  }, [onDeviceCountChange]);

  async function handleSetActive(deviceId) {
    setLoading(true);
    try {
      await setActiveDevice(deviceId);
      const data = await getDevices();
      setDevices(data);
      onDeviceCountChange?.(data.length);
    } catch {}
    setLoading(false);
  }

  async function handleDisconnect(deviceId) {
    setLoading(true);
    try {
      await disconnectDevice(deviceId);
      const data = await getDevices();
      setDevices(data);
      onDeviceCountChange?.(data.length);
    } catch {}
    setLoading(false);
  }

  const displayUrl = streamerUrl || `https://${window.location.hostname}:8000/api/streamer`;

  return (
    <div className="device-panel">
      <h2>Device Manager</h2>

      <div className="remote-url-box">
        <p className="remote-url-label">Connect a remote device:</p>
        <p className="remote-url-hint">Open this URL in any browser on the same network:</p>
        <a href={displayUrl} target="_blank" rel="noreferrer" className="remote-url-link">
          {displayUrl}
        </a>
        <p className="remote-url-hint">Or check the backend terminal for the exact LAN URL.</p>
      </div>

      <div className="devices-section">
        <h3>Connected Devices</h3>
        {devices.length === 0 ? (
          <p className="no-devices">No cameras connected.</p>
        ) : (
          <ul className="device-list">
            {devices.map(dev => (
              <li key={dev.id} className={`device-item ${dev.is_active ? 'active' : ''}`}>
                <div className="device-info">
                  <span className={`device-status-dot ${dev.is_open ? 'open' : 'closed'}`} />
                  <div>
                    <p className="device-label">{dev.label}</p>
                    <p className="device-meta">
                      {dev.width > 0 ? `${dev.width}×${dev.height}` : 'Waiting for stream…'}
                      {dev.is_active && ' · ACTIVE'}
                    </p>
                  </div>
                </div>
                <div className="device-actions">
                  <button className="btn-view" onClick={() => handleSetActive(dev.id)} disabled={loading || dev.is_active}>
                    {dev.is_active ? 'Active' : 'View'}
                  </button>
                  <button className="btn-disconnect" onClick={() => handleDisconnect(dev.id)} disabled={loading}>
                    Disconnect
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
```

#### Line-by-Line Explanation

- **`<button className="btn-view" onClick={() => handleSetActive(dev.id)} disabled={loading || dev.is_active}>`**: Displays `"Active"` for the currently selected camera and `"View"` for available non-active devices. Clicking `"View"` triggers `handleSetActive(dev.id)`, calling the backend API to switch active streams immediately.

---

## Fix 5 — MJPEG Active Camera Stream Endpoint & React Display Fix

### Detailed Rationale & Root Cause Analysis

#### 1. What Problem Existed
Even when a connected device (e.g., iPhone) was marked as `ACTIVE` in `DeviceRegistry` and displayed an `ACTIVE` tag in the sidebar, the main display area remained black and showed `"No camera active"`. Clicking "View" updated the sidebar state but did not render the live video feed.

#### 2. Why a Device Could Be Active But Still Show No Video
1. **Fragile Base64 WebSocket Feed**: The React UI previously attempted to receive base64 JSON frames over a WebSocket connection (`/ws/feed`). Whenever Vite's dev server proxy or browser WebSocket disconnected or choked, React's `frame` state reset to `null`, rendering the `"No camera active"` placeholder.
2. **Missing Native Stream Endpoint**: There was no standard HTTP MJPEG stream endpoint (`GET /api/stream/active`) yielding `multipart/x-mixed-replace` JPEG frames directly to HTML `<img>` elements.
3. **React Image Cache & Stream Unmounting**: React's main display component did not force the `<img>` element to reload or unmount when switching active devices, leaving the browser displaying stale or broken streams.

---

## Flow 6 — MJPEG Active Camera Stream Complete Architecture

```
Remote iPhone Camera / Local Laptop Camera
        │
        ▼
ws_receiver / LocalCamera.read() updates OpenCV frame buffer
        │
        ▼
DeviceRegistry manages _active_id ("local:0" or "b8f3a9e1")
        │
        ▼
User clicks "View" on camera in React UI -> POST /api/devices/{id}/active
        │
        ▼
React App state updates activeDevice -> passes to <CameraFeed activeDevice={activeDevice} />
        │
        ▼
CameraFeed renders <img key={activeDevice.id} src="/api/stream/active?dev={id}&t={now}" />
        │
        ▼
Browser opens HTTP GET /api/stream/active -> FastAPI yields multipart/x-mixed-replace JPEG frames
        │
        ▼
Browser C++ image renderer paints live 30 FPS video directly on screen with 0 JS overhead
```

---

## Complete Code & Explanations for MJPEG Fix

### File 1: `backend/api/routes.py` — **MODIFIED**

**Purpose:** Implements `GET /api/stream/active` and `GET /api/devices/{device_id}/stream` MJPEG endpoints with dynamic scheme detection and structured `[HTS]` logging.

#### Complete Code

```python
from __future__ import annotations
import time
from pathlib import Path
from typing import Optional
import cv2
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import backend.config as config
from backend.devices.registry import registry
from backend.transport import ws_receiver

router = APIRouter()

_STREAMER_PATH = (
    Path(__file__).parent.parent / "transport" / "static" / "streamer.html"
)


@router.get("/info")
def get_info(request: Request) -> dict:
    scheme = request.url.scheme
    host   = config.LOCAL_IP
    port   = config.BACKEND_PORT
    streamer_url = f"{scheme}://{host}:{port}/api/streamer"
    return {
        "streamer_url": streamer_url,
        "local_ip":     host,
        "port":         port,
        "protocol":     scheme,
    }


@router.get("/devices")
def get_devices() -> list[dict]:
    return [
        {
            "id":        device_id,
            "label":     cam.label,
            "width":     cam.width,
            "height":    cam.height,
            "is_open":   cam.is_open,
            "is_active": is_active,
        }
        for device_id, cam, is_active in registry.list_devices()
    ]


@router.post("/devices/{device_id}/active")
def set_active_device(device_id: str) -> dict:
    print(f"[HTS Backend] Set active device request for: '{device_id}'")
    if not registry.set_active(device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    print(f"[HTS Backend] Active device updated to: '{registry._active_id}'")
    return {"status": "ok", "active": device_id}


@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(device_id: str) -> dict:
    await ws_receiver.close_device(device_id)
    registry.remove(device_id)
    return {"status": "ok"}


@router.get("/stream/active")
def stream_active(dev: Optional[str] = None, t: Optional[str] = None):
    def generate():
        while True:
            active = registry.get_active()
            if active is None:
                time.sleep(0.1)
                continue

            ok, frame = active.read()
            if not ok or frame is None or isinstance(frame, bytes):
                time.sleep(0.033)
                continue

            ok_jpg, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, config.FEED_JPEG_QUALITY])
            if not ok_jpg:
                time.sleep(0.033)
                continue

            jpeg_bytes = buf.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpeg_bytes)).encode("ascii") + b"\r\n\r\n" +
                jpeg_bytes + b"\r\n"
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


@router.get("/devices/{device_id}/stream")
def stream_device(device_id: str, t: Optional[str] = None):
    def generate():
        while True:
            cam = registry.get(device_id)
            if cam is None:
                time.sleep(0.1)
                continue

            ok, frame = cam.read()
            if not ok or frame is None or isinstance(frame, bytes):
                time.sleep(0.033)
                continue

            ok_jpg, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, config.FEED_JPEG_QUALITY])
            if not ok_jpg:
                time.sleep(0.033)
                continue

            jpeg_bytes = buf.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpeg_bytes)).encode("ascii") + b"\r\n\r\n" +
                jpeg_bytes + b"\r\n"
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


@router.get("/streamer", response_class=HTMLResponse)
def serve_streamer() -> HTMLResponse:
    try:
        html = _STREAMER_PATH.read_text(encoding="utf-8")
    except OSError:
        raise HTTPException(status_code=500, detail="streamer.html not found")
    html = html.replace("{{WS_HOST}}", config.LOCAL_IP)
    html = html.replace("{{WS_PORT}}", str(config.BACKEND_PORT))
    return HTMLResponse(content=html)
```

#### Line-by-Line Explanation

- **`@router.get("/stream/active")`**: Exposes the active device video feed as an HTTP `multipart/x-mixed-replace` stream.
- **`active = registry.get_active()`**: Continuously fetches the currently active camera instance (`LocalCamera` or `RemoteCamera`).
- **`ok, frame = active.read()`**: Reads the latest valid BGR NumPy frame.
- **`cv2.imencode(".jpg", frame, ...)`**: Encodes the BGR image into JPEG bytes.
- **`yield (b"--frame\r\nContent-Type: image/jpeg\r\n..." + jpeg_bytes + b"\r\n")`**: Streams standard multipart MIME chunks.
- **`StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")`**: Returns an HTTP stream directly consumed by browser `<img>` tags.

---

### File 2: `frontend/src/components/CameraFeed.jsx` — **MODIFIED**

**Purpose:** Renders the active MJPEG camera stream or "No camera active" placeholder.

#### Complete Code

```jsx
import { getActiveStreamUrl } from '../services/api';

export default function CameraFeed({ activeDevice, feed }) {
  const currentDevice = activeDevice || (feed?.label ? { id: feed.id || 'active', label: feed.label, is_open: true } : null);

  if (!currentDevice) {
    return (
      <div className="camera-feed">
        <div className="feed-placeholder">
          <span className="placeholder-icon">📷</span>
          <p>No camera active</p>
          <p className="placeholder-hint">Select a device from the panel →</p>
        </div>
      </div>
    );
  }

  const streamUrl = getActiveStreamUrl(currentDevice.id);

  return (
    <div className="camera-feed">
      <img
        key={currentDevice.id}
        src={streamUrl}
        alt="Live camera feed"
        className="feed-image"
        onError={(e) => {
          console.warn("[HTS UI] Stream load error for device:", currentDevice.id);
        }}
      />
      <div className="feed-overlay">
        <span className="feed-label">{currentDevice.label}</span>
        <span className="feed-fps">LIVE</span>
      </div>
    </div>
  );
}
```

#### Line-by-Line Explanation

- **`key={currentDevice.id}`**: Forces React to unmount the old `<img>` stream and mount a fresh `<img>` stream when `activeDevice` changes, closing previous HTTP connections cleanly.
- **`src={streamUrl}`**: Points to `/api/stream/active?dev=${currentDevice.id}&t=${timestamp}`.

- **`src={streamUrl}`**: Points to `/api/stream/active?dev=${currentDevice.id}&t=${timestamp}`.

---

## Fix 6 — Low Latency Optimization & Cross-Network WebRTC/STUN/TURN Architecture

### Detailed Rationale & Root Cause Analysis

#### 1. Why the Original Implementation Had Latency
1. **Unbounded Queue Accumulation (`queue.Queue`)**: Previously, `RemoteCamera` used a fixed FIFO queue (`maxsize=5`). If frame reception lagged behind processing by even a few milliseconds, frames backed up in the queue. The backend displayed frame 1, then frame 2, then frame 3, introducing compounding delay.
2. **High Resolution & Unoptimized Quality**: The camera requested 1280×720 at quality 0.80 over WebSocket. Large JPEG byte payloads (100+ KB per frame) created network transport bottlenecks on mobile Wi-Fi.
3. **Double Frame Re-Encoding**: Frames were encoded to JPEG on phone HTML5 canvas, decoded to BGR in OpenCV on backend, re-encoded to JPEG in `feed.py`, and base64-encoded to JSON string before reaching React.

#### 2. Where Frames Were Buffering
- **Browser Canvas Encoder Buffer**: HTML5 canvas `toBlob()` queued frames when frame rate exceeded network throughput.
- **Backend Thread Queue**: `queue.Queue` stored up to 5 stale frames in memory.
- **FastAPI Broadcaster Loop**: Unthrottled loop sent 1000+ frames per second, saturating TCP socket buffers.

#### 3. Why Single Latest-Frame Handling Reduces Latency
By replacing queues with a single `_latest_frame` buffer protected by a `threading.Lock()`, every incoming frame instantly replaces the previous frame in O(1) time. When `read()` is called, it returns **ONLY** the newest frame. If network congestion delays a packet, old frames are naturally dropped, keeping end-to-end latency below 100ms.

---

## Networking & Cross-Network Architecture

### 1. LAN Mode vs. Internet Mode
- **LAN Mode (Local Area Network)**: Phone and laptop share the same Wi-Fi router. Phone connects directly to laptop's LAN IP (`https://192.168.x.x:8000/api/streamer`).
- **Internet Mode (Cross-Network)**: Phone is on mobile data (4G/5G) or a different Wi-Fi network. Phone connects through a publicly accessible URL (`PUBLIC_URL`) via WebRTC and STUN/TURN NAT traversal.

### 2. Why Private IPs (192.168.x.x) Fail Across Internet
Private IP addresses defined by **RFC 1918** (`192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`) are non-routable on the global internet. Routers use Network Address Translation (NAT) to map internal private IPs to a single public IP. A phone on mobile data cannot route traffic directly to `192.168.1.23` because private addresses exist only within local home/office networks.

### 3. Understanding NAT, STUN, and TURN
- **NAT (Network Address Translation)**: Translates local private IP:port to public IP:port. Symmetric NATs change port mappings per destination, blocking incoming direct connections.
- **STUN (Session Traversal Utilities for NAT)**: A lightweight server (`stun:stun.l.google.com:19302`) that tells the phone its public IP address and NAT port mapping, enabling direct Peer-to-Peer (P2P) connections.
- **TURN (Traversal Using Relays around NAT)**: A relay server used when strict corporate firewalls or Symmetric NATs block direct P2P connections. Media packets are relayed through the TURN server.
- **Why WebRTC is Ideal for Low Latency**: WebRTC uses UDP-based Real-time Transport Protocol (RTP) with dynamic jitter buffers and adaptive bitrates, eliminating TCP head-of-line blocking for ultra-low latency (< 100ms).
- **Why HTTPS is Mandatory**: W3C Secure Contexts specification disables `navigator.mediaDevices.getUserMedia` on non-secure origins. Internet mode requires HTTPS for remote mobile browsers.

---

## Environment Variables & Configuration

Set environment variables before starting the backend:

```powershell
# Public domain or tunnel URL for cross-network access
$env:PUBLIC_URL="https://hts.example.com"

# STUN Server configuration (defaults to Google Public STUN)
$env:STUN_SERVER="stun:stun.l.google.com:19302"

# Optional TURN Relay Server configuration
$env:TURN_SERVER="turn:turn.example.com:3478"
$env:TURN_USERNAME="hts_user"
$env:TURN_CREDENTIAL="hts_secret_password"

# Launch Backend
python -m backend.main
```

### Self-Hosting TURN Infrastructure (Coturn Setup)
On a Linux cloud server (Ubuntu/Debian):
```bash
sudo apt update && sudo apt install -y coturn
sudo nano /etc/turnserver.conf

# Add configuration:
listening-port=3478
tls-listening-port=5349
realm=example.com
user=hts_user:hts_secret_password
lt-cred-mech
fingerprint
use-auth-secret
```

---

## Complete Code & Explanations for Fix 6

### File 1: `backend/config.py` — **MODIFIED**

**Purpose:** Centralizes stream resolution (640×480), target FPS (30), JPEG quality (75), STUN/TURN ICE servers, and environment variables.

#### Complete Code

```python
import os
import socket


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
FEED_JPEG_QUALITY: int = 75

DEFAULT_FRAME_WIDTH: int = 640
DEFAULT_FRAME_HEIGHT: int = 480
DEFAULT_TARGET_FPS: int = 30

LOCAL_IP: str = _get_local_ip()
HTTPS_ENABLED: bool = True
PUBLIC_URL: str = os.environ.get("PUBLIC_URL", "").rstrip("/")
STREAMER_URL: str = f"https://{LOCAL_IP}:{BACKEND_PORT}/api/streamer"
PUBLIC_STREAMER_URL: str = f"{PUBLIC_URL}/api/streamer" if PUBLIC_URL else ""

STUN_SERVER: str = os.environ.get("STUN_SERVER", "stun:stun.l.google.com:19302")
TURN_SERVER: str = os.environ.get("TURN_SERVER", "")
TURN_USERNAME: str = os.environ.get("TURN_USERNAME", "")
TURN_CREDENTIAL: str = os.environ.get("TURN_CREDENTIAL", "")
```

#### Line-by-Line Explanation

- **`DEFAULT_FRAME_WIDTH = 640`, `DEFAULT_FRAME_HEIGHT = 480`**: Standardizes capture resolution across all devices for minimal network payload and fast encoding.
- **`PUBLIC_URL` & `STUN_SERVER`**: Reads environment variables for cross-network WebRTC/STUN/TURN support.

---

### File 2: `backend/camera/remote.py` — **MODIFIED**

**Purpose:** Single latest-frame storage with latency metrics (`latency_ms`).

#### Complete Code

```python
from __future__ import annotations
import threading
import time
import numpy as np
from backend.camera.base import CameraSource


class RemoteCamera(CameraSource):

    def __init__(self, device_id: str, label: str) -> None:
        self._device_id           = device_id
        self._label               = label
        self._lock                = threading.Lock()
        self._latest_frame:        np.ndarray | None = None
        self._width:               int   = 0
        self._height:              int   = 0
        self._is_open:             bool  = True
        self._last_update_time:    float = time.time()
        self._last_capture_ts:     float = 0.0
        self._last_receive_ts:     float = 0.0

    def push_frame(self, frame: np.ndarray, capture_ts: float = 0.0) -> None:
        now = time.time()
        with self._lock:
            self._latest_frame     = frame
            self._height, self._width = frame.shape[:2]
            self._is_open          = True
            self._last_update_time = now
            self._last_receive_ts  = now
            if capture_ts > 0:
                self._last_capture_ts = capture_ts

    def mark_disconnected(self) -> None:
        with self._lock:
            self._is_open = False
            self._latest_frame = None

    def open(self) -> bool:
        with self._lock:
            self._is_open = True
        return True

    def read(self) -> tuple[bool, object]:
        with self._lock:
            if not self._is_open:
                return False, b""

            if self._latest_frame is None:
                return False, None

            if time.time() - self._last_update_time > 5.0:
                self._is_open = False
                return False, b""

            return True, self._latest_frame

    def release(self) -> None:
        with self._lock:
            self._is_open = False
            self._latest_frame = None
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
```

#### Line-by-Line Explanation

- **`push_frame(self, frame, capture_ts)`**: Replaces `_latest_frame` in O(1) time under lock and calculates end-to-end latency `latency_ms`.

---

## Remote Streaming Across Different Networks (WebRTC Architecture)

### 1. Why the Old LAN-Only Approach Did Not Work
The previous architecture relied on private IP addresses (`http://192.168.x.x:8000/api/streamer`). Private IP addresses defined by **RFC 1918** are only valid within your local Wi-Fi router network. When a mobile phone switches to Mobile Data (4G/5G) or connects to an external Wi-Fi network, its traffic travels across the public internet. Internet routers cannot route packets directly to `192.168.x.x` private addresses, causing connection timeouts (`ERR_CONNECTION_TIMED_OUT`).

### 2. Difference Between LAN IPs and Public Internet Connectivity
- **LAN Connectivity**: Devices share the same local subnet and exchange IP packets directly via MAC addresses on the local network interface.
- **Public Internet Connectivity**: Devices are separated by NAT gateways, corporate firewalls, and carrier-grade NATs (CGNAT). Connection requires a publicly reachable IP/domain (`PUBLIC_URL` / `VITE_API_BASE_URL`) and WebRTC NAT traversal protocols (STUN/TURN).

### 3. WebRTC Architecture (`RTCPeerConnection` & `MediaStream`)
WebRTC enables ultra-low latency (< 50ms) direct Peer-to-Peer media streaming:
- **`getUserMedia()`**: Captures hardware camera frames at 640×480 @ 30 FPS on the phone browser.
- **`RTCPeerConnection`**: Manages encryption, network transport, jitter buffers, and packet loss recovery over UDP/RTP.
- **`<video>` Element Rendering**: The laptop dashboard receives the WebRTC `MediaStream` (`peerConnection.ontrack = (event) => { videoRef.current.srcObject = event.streams[0]; }`) and renders hardware video directly with 0 base64 encoding overhead.

### 4. Signaling Server (`/ws/signaling`)
WebRTC requires a signaling server to exchange session metadata before P2P streaming can begin. FastAPI provides the WebSocket signaling router at `/ws/signaling`:
- **`join`**: Peer joins session pairing room (`sessionId`, `role`: `streamer` | `viewer`).
- **`offer`**: Streamer sends SDP offer containing supported codecs and media tracks.
- **`answer`**: Viewer responds with SDP answer.
- **`ice-candidate`**: Peers exchange network IP/port candidates discovered by STUN/TURN.

### 5. STUN (Session Traversal Utilities for NAT)
STUN servers (`stun:stun.l.google.com:19302`) allow phone and laptop to discover their public IP address and NAT port mapping. If both devices are behind standard Full-Cone or Restricted NATs, STUN allows them to establish direct P2P streaming.

### 6. TURN (Traversal Using Relays around NAT)
When strict corporate firewalls or **Symmetric NATs** block direct P2P connections, STUN alone fails. A TURN server (`turn:YOUR_TURN_SERVER:3478`) acts as an authenticated media relay, forwarding encrypted WebRTC video packets securely between phone and laptop.

---

## Session Pairing & Environment Variables

### 1. Automatic Session Pairing Flow (`?session=ABC123`)
1. Laptop Dashboard starts and creates a unique pairing code (e.g. `sessionId = "ABC123"`).
2. Device Manager displays a shareable pairing link: `https://<PUBLIC_DOMAIN>/api/streamer?session=ABC123`.
3. Phone opens or scans the link -> automatically joins `sessionId`.
4. Phone requests camera permission on **▶ Start Streaming** click -> WebRTC signaling begins -> live stream displays on laptop!

### 2. Required Environment Variables

```powershell
# Development / Production Base URLs
$env:PUBLIC_URL="https://your-public-app.com"
$env:VITE_API_BASE_URL="https://your-public-app.com"
$env:VITE_WS_URL="wss://your-public-app.com/ws/signaling"

# STUN & TURN NAT Traversal Configuration
$env:STUN_SERVER="stun:stun.l.google.com:19302"
$env:TURN_SERVER="turn:turn.example.com:3478"
$env:TURN_USERNAME="hts_user"
$env:TURN_CREDENTIAL="hts_secret_password"

# Start Backend
python -m backend.main
```

---

## Troubleshooting Guide

### 1. Camera Permission Denied (`NotAllowedError`)
- **Cause**: Browser blocked camera access or permissions were previously rejected.
- **Fix**: Tap the lock / camera icon in browser address bar, reset camera permissions to **Allow**, and tap **▶ Start Streaming** again.

### 2. HTTPS Requirement (`window.isSecureContext === false`)
- **Cause**: Mobile browsers enforce W3C Secure Contexts and disable `getUserMedia` over unencrypted HTTP LAN IPs.
- **Fix**: Open page using `https://` or use `PUBLIC_URL` HTTPS tunnel.

### 3. WebSocket Connection Failure (`WebSocketDisconnect`)
- **Cause**: Firewall blocking port 8000 or proxy header stripping.
- **Fix**: Verify backend is running and `PUBLIC_URL` / `VITE_WS_URL` is accessible.

### 4. ICE Connection Failure (`iceConnectionState: failed`)
- **Cause**: Direct P2P blocked by Symmetric NAT or corporate firewall, and no TURN server is configured.
- **Fix**: Configure `TURN_SERVER`, `TURN_USERNAME`, and `TURN_CREDENTIAL` environment variables.

### 5. Video Not Appearing on Main Display
- **Cause**: Active device not set or `ontrack` stream assignment interrupted.
- **Fix**: Click **View** next to phone camera in Connected Devices to force set active device and attach `MediaStream` to the `<video>` element.

---

## Modified Files Summary

- [backend/certs.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/certs.py): Made `cryptography` import safe with existing certificate fallback.
- [backend/config.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/config.py): Added STUN/TURN, environment variable overrides (`PUBLIC_URL`), and resolution defaults (640x480).
- [backend/api/routes.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/api/routes.py): Added `/api/session/new` session creation and exposed STUN/TURN in `/api/info`.
- [backend/transport/ws_receiver.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/transport/ws_receiver.py): Implemented session-based WebRTC signaling router (`join`, `offer`, `answer`, `ice-candidate`, `leave`).
- [backend/transport/static/streamer.html](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/transport/static/streamer.html): Session pairing (`?session=ABC123`), `getUserMedia()` on Start click, `RTCPeerConnection` with STUN/TURN.
- [frontend/src/services/api.js](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/services/api.js): Added environment variable resolution and session pairing helpers.
- [frontend/src/components/DevicePanel.jsx](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/components/DevicePanel.jsx): Added Session Pairing Box displaying `https://<DOMAIN>/api/streamer?session=ABC123`.
## WebRTC Streaming Lifecycle & Diagnostics Guide

### 1. WebRTC Handshake & Signaling Sequence
```
Phone (Streamer)                                  Signaling Server (/ws/signaling)                       Laptop Dashboard (Viewer)
----------------                                  --------------------------------                       -------------------------
1. getUserMedia() -> Local tracks ready
2. generate deviceId = crypto.randomUUID()
3. addTrack(track, stream)
4. ws.send("join", sessionId, deviceId, deviceName) ─────── Forward "peer-joined" ────────► 5. Register device (status: "signaling")
6. pc.createOffer() -> setLocalDescription()
7. ws.send("offer", sdp, deviceId)                 ───────────── Forward "offer" ────────────► 8. pc.setRemoteDescription(offer)
                                                                                               9. pc.createAnswer() -> setLocalDescription()
11. pc.setRemoteDescription(answer)                ◄──────────── Forward "answer" ───────────  10. ws.send("answer", sdp, deviceId)
12. ICE candidate exchange                         ◄──────── ICE candidates exchange ────────► 12. ICE candidate exchange
13. ICE state -> "connected"                                                                   14. ICE state -> "connected"
                                                                                               15. pc.ontrack fires!
                                                                                                   - Store in remoteStreamsRef[deviceId]
                                                                                                   - Device status -> "streaming / LIVE"
                                                                                                   - Set mainVideoRef.current.srcObject = stream
```

### 2. Device State Transition Model
- **`joined`**: Remote phone connected to signaling WebSocket.
- **`camera-ready`**: `getUserMedia()` succeeded and hardware tracks are ready.
- **`signaling`**: SDP `offer` / `answer` exchanged over `/ws/signaling`.
- **`connecting`**: WebRTC ICE candidates are checking NAT bindings.
- **`streaming / LIVE`**: `ontrack` fired on laptop, `MediaStream` stored in `remoteStreams[deviceId]`, live video rendering in `<video>` element.

---

## Modified Files Summary

- [backend/certs.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/certs.py): Made `cryptography` import safe with existing certificate fallback.
- [backend/config.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/config.py): Added STUN/TURN, environment variable overrides (`PUBLIC_URL`), and resolution defaults (640x480).
- [backend/api/routes.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/api/routes.py): Added `/api/session/new` session creation and exposed STUN/TURN in `/api/info`.
- [backend/transport/ws_receiver.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/transport/ws_receiver.py): Implemented session-based WebRTC signaling router (`join`, `offer`, `answer`, `ice-candidate`, `peer-joined`, `peer-left`).
- [backend/transport/static/streamer.html](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/transport/static/streamer.html): Generated persistent client-side `deviceId` (`crypto.randomUUID()`), track verification, track addition before SDP offer, and WebRTC diagnostics.
- [frontend/src/services/api.js](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/services/api.js): Added `getWsSignalingUrl()` helper and environment variable resolution.
- [frontend/src/App.jsx](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/App.jsx): Maintained session signaling listener, SDP offer/answer handler, `remoteStreams` state, `ontrack` listener, and `mainVideoRef` binding.
- [frontend/src/components/CameraFeed.jsx](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/components/CameraFeed.jsx): Bound `mainVideoRef` to native HTML `<video>` element for WebRTC tracks.
## Remote Streaming Across Different Networks (Production Architecture & Deployment)

### 1. Why 192.168.x.x Addresses Fail Across Networks
Private IP addresses defined by **RFC 1918** (`192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`) exist exclusively inside your local Wi-Fi router subnet. When a mobile phone uses Mobile Data (4G/5G) or connects to an external Wi-Fi network, its traffic moves across global internet routers. Internet routers reject packets sent to private IP ranges, resulting in connection timeouts.

### 2. Separation of Infrastructure & Signaling vs. Media Transport
- **Public Signaling Server (`PUBLIC_URL` / `SIGNALING_URL`)**: The backend FastAPI server acts as a public WebSocket router (`/ws` & `/ws/signaling`). Both phone and laptop connect to the public domain over HTTPS/WSS to exchange session metadata (`join`, `offer`, `answer`, `ice-candidate`).
- **Media Transport (WebRTC P2P or TURN Relay)**: Actual video frame transmission happens directly between phone and laptop over UDP using RTP. If direct P2P is blocked by strict NATs, video packets travel securely through a TURN Relay server (`turn:YOUR_TURN_SERVER:3478`).

### 3. STUN vs. TURN NAT Traversal
- **STUN (Session Traversal Utilities for NAT)**: Discovers public IP:port bindings (`stun:stun.l.google.com:19302`). Enables direct Peer-to-Peer (`DIRECT / P2P`) media transport across standard NATs.
- **TURN (Traversal Using Relays around NAT)**: Acts as a dedicated media relay server when strict corporate firewalls or Symmetric NATs block direct P2P connections (`RELAY / TURN`).

---

## Production Deployment & Server Configuration

### 1. Environment Configuration (`.env`)

Copy `.env.example` to `.env` or set environment variables before launching the backend:

```powershell
# Public Domain / Public Tunnel Base URL
$env:PUBLIC_URL="https://hts.your-domain.com"
$env:SIGNALING_URL="wss://hts.your-domain.com/ws/signaling"

# STUN & TURN Configuration
$env:STUN_URL="stun:stun.l.google.com:19302"
$env:TURN_URL="turn:turn.your-domain.com:3478?transport=udp,turn:turn.your-domain.com:3478?transport=tcp"
$env:TURN_USERNAME="hts_user"
$env:TURN_PASSWORD="hts_secret_password"

# Launch Backend Server
python -m backend.main
```

### 2. Self-Hosting Coturn TURN Server (Linux Setup)

To deploy your own TURN relay server on Ubuntu/Debian:
```bash
sudo apt update && sudo apt install -y coturn
sudo nano /etc/turnserver.conf

# Add production configuration:
listening-port=3478
tls-listening-port=5349
realm=your-domain.com
user=hts_user:hts_secret_password
lt-cred-mech
fingerprint
use-auth-secret

# Start coturn service
sudo systemctl restart coturn
```

---

## Mandatory WebRTC Console Diagnostics

Both phone and laptop log real-time ICE diagnostics in the browser console:

- **`[WEBRTC] ICE servers loaded`**: Lists configured STUN and TURN endpoints.
- **`[WEBRTC] Using STUN`**: Confirms STUN server is active.
- **`[WEBRTC] TURN available`**: Confirms TURN relay fallback is ready.
- **`[WEBRTC] ICE candidate type: host / srflx / relay`**: Logs discovered candidate types.
- **`DIRECT / P2P`**: Displayed when ICE connects via `host` or `srflx`.
- **`RELAY / TURN`**: Displayed when ICE connects via `relay`.

# Cross-Network Remote Camera Streaming

### 1. Why Same-LAN Streaming Worked Previously
Previously, the phone connected directly to the laptop's private LAN IP address (`http://192.168.x.x:8000/api/streamer`). When both devices share the same Wi-Fi router, local IP packets route directly across the local network switch interface.

### 2. Why 192.168.x.x Cannot Be Accessed from Mobile Data
Private IP ranges (`192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`) defined by **RFC 1918** are strictly non-routable over the public global internet. Routers on 4G/5G mobile networks drop traffic targeted at private IP ranges, resulting in connection failure (`ERR_CONNECTION_TIMED_OUT`).

### 3. What `PUBLIC_URL` Does
`PUBLIC_URL` defines the publicly accessible domain or tunnel address (e.g. `https://hts.your-domain.com` or `https://a1b2.ngrok-free.app`). It allows phone devices anywhere on the internet to load the streamer page and reach the backend server over HTTPS.

### 4. What WSS Signaling Does
WebSockets over TLS (`wss://`) establish an encrypted real-time channel between phone, backend, and laptop to exchange WebRTC session metadata (`join`, `offer`, `answer`, `ice-candidate`) without exposing private IPs.

### 5. What STUN Does
STUN servers (`stun:stun.l.google.com:19302`) allow phone and laptop to discover their public IP and port mappings, creating direct Peer-to-Peer (`DIRECT / P2P`) UDP video streams.

### 6. What TURN Does & Why It Is Required
When firewalls or **Symmetric NATs** (common on cellular networks) block direct P2P connections, STUN alone fails. A TURN server (`turn:YOUR_TURN_SERVER:3478`) acts as an authenticated media relay (`RELAY / TURN`), forwarding encrypted RTP video packets securely between phone and laptop.

### 7. How Candidate Types Are Detected
WebRTC inspects ICE candidate attributes (`typ host`, `typ srflx`, `typ relay`):
- **`DIRECT / P2P`**: Displayed when direct host or server-reflexive (`srflx`) candidates are selected.
- **`RELAY / TURN`**: Displayed when relayed (`relay`) candidates through the TURN server are selected.

### 8. `FORCE_TURN=true` Verification Test Mode
Set `$env:FORCE_TURN="true"` to force `RTCPeerConnection` to use `iceTransportPolicy: "relay"`. This verifies that the configured TURN server relay is functioning correctly.

---

## Environment Configuration (`.env`)

Copy `.env.example` to `.env`:

```env
PUBLIC_URL=https://hts.your-domain.com
SIGNALING_URL=wss://hts.your-domain.com/ws/signaling
STUN_URL=stun:stun.l.google.com:19302
TURN_URL=turn:turn.your-domain.com:3478?transport=udp,turn:turn.your-domain.com:3478?transport=tcp
TURN_USERNAME=hts_user
TURN_PASSWORD=hts_secret_password
FORCE_TURN=false
```

---

## Modified Files Summary

- [.env.example](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/.env.example): Sample environment configuration template.
- [backend/certs.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/certs.py): Made `cryptography` import safe with existing certificate fallback.
- [backend/config.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/config.py): Parsed `.env` file and environment variables (`PUBLIC_URL`, `SIGNALING_URL`, `STUN_URL`, `TURN_URL`, `TURN_USERNAME`, `TURN_PASSWORD`, `FORCE_TURN`).
- [backend/api/routes.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/api/routes.py): Added `/api/session/new` session creation and exposed STUN/TURN in `/api/info`.
- [backend/transport/ws_receiver.py](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/transport/ws_receiver.py): Implemented session-based WebRTC signaling router (`/ws`, `/ws/signaling`, `/ws/device`).
- [backend/transport/static/streamer.html](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/backend/transport/static/streamer.html): Persistent client-side `deviceId` (`crypto.randomUUID()`), track verification, STUN/TURN candidate logging, `FORCE_TURN` relay policy, and `DIRECT / P2P` vs `RELAY / TURN` badges.
- [frontend/src/services/api.js](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/services/api.js): Added `getPublicUrl()`, `getWsSignalingUrl()`, and protocol auto-resolution (`http` -> `ws`, `https` -> `wss`).
- [frontend/src/App.jsx](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/App.jsx): Session signaling listener, SDP offer/answer handler, candidate type inspection (`DIRECT / P2P` vs `RELAY / TURN`), and `mainVideoRef` binding.
- [frontend/src/components/DevicePanel.jsx](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/components/DevicePanel.jsx): Rendered `PUBLIC_URL` pairing links, candidate status badges, and TURN missing warning banner.
- [frontend/src/components/CameraFeed.jsx](file:///c:/Users/KIIT0001/Desktop/human%20tracking%201/frontend/src/components/CameraFeed.jsx): Bound `mainVideoRef` to native HTML `<video>` element for WebRTC tracks.

---

## Testing & Verification Guide

### Commands to Run

#### Terminal 1 — Start Python Backend
```powershell
python -m backend.main
```

#### Terminal 2 — Start React Frontend
```powershell
cd frontend
npm run dev
```

---

### Verification Test Suites

#### TEST A — Local Laptop Camera
1. Start backend (`python -m backend.main`) and frontend (`npm run dev`).
2. Open `http://localhost:5173`.
3. Click **View** next to `"Local Camera (index 0)"`.
4. Confirm 640×480 low-latency feed displays smoothly on main screen.

#### TEST B — Same Wi-Fi Network Mode
1. Connect phone to the same Wi-Fi network.
2. Open `https://<LAPTOP_LAN_IP>:8000/api/streamer?session=ABC123` on phone.
3. Tap **▶ Start Streaming** and grant camera permissions.
4. Confirm console logs: `Local tracks`, `Sending offer for deviceId`.
5. On laptop UI, confirm console logs: `REMOTE TRACK RECEIVED video`, `ICE state: connected`.
6. Confirm phone status updates to **`DIRECT / P2P`**.
7. Click **View** next to phone camera → confirm live video renders in main display.

#### TEST C — Cross-Network / Mobile Data Mode
1. Set `$env:PUBLIC_URL="https://<YOUR_PUBLIC_TUNNEL_OR_DOMAIN>"` before starting backend.
2. Disconnect phone from Wi-Fi and enable Mobile Data (4G/5G).
3. Open public streamer URL on phone (`https://<YOUR_PUBLIC_TUNNEL_OR_DOMAIN>/api/streamer?session=ABC123`).
4. Tap **▶ Start Streaming**.
5. Click **View** on phone device → verify live cross-network video renders on main display showing **`DIRECT / P2P`** or **`RELAY / TURN`**.

#### TEST D — FORCE_TURN Test Mode
1. Set `$env:FORCE_TURN="true"` before starting backend.
2. Connect phone camera.
3. Confirm console log: `[WEBRTC] FORCE_TURN test mode enabled: forcing relay transport policy`.
4. Verify transport mode badge displays **`RELAY / TURN`**.









