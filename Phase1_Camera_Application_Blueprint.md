# Phase 1 Blueprint: Standalone Camera Application
### Human Tracking System — Development Guide

> **Disclaimer:** This is just the first step, and there are many more to go.

---

## How to Use This Document

Every step in this guide follows the same pattern:

1. **IMPLEMENT** — The exact code block you will write for that step.
2. **UNDERSTAND** — A deep explanation of every concept, keyword, and mechanism in that code.

Work through each step in order. Do not skip the UNDERSTAND sections — they are what will let you build the next phases without help.

---

## Project File Structure

Before writing any code, create this folder and file layout inside your project directory:

```
Human Tracking/
│
├── venv/                    ← created by you (Step 1)
├── phase1_camera/
│   ├── __init__.py          ← created in Step 2
│   ├── camera_capture.py    ← written in Steps 3–5
│   └── camera_app.py        ← written in Steps 6–10
└── requirements.txt         ← created in Step 2
```

---

---

## STEP 1 — Create and Activate a Virtual Environment

### IMPLEMENT

Run these commands in your terminal, inside your project folder:

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Your terminal prompt should now start with `(venv)`.

---

### UNDERSTAND

**What is `python -m venv`?**
The `-m` flag tells Python to run a module as a script. `venv` is a standard library module that ships with Python — you don't install it separately. Running `python -m venv venv` invokes this module and tells it to create a new virtual environment in a folder called `venv`.

**What is a virtual environment?**
A virtual environment is a self-contained copy of the Python interpreter and a fresh, empty `site-packages` directory. When you install libraries inside it, they go into *this* folder, not into your system-wide Python installation. This means:
- Different projects can use different library versions without conflicting.
- Your project can be reproduced exactly on another machine using `requirements.txt`.
- Deleting the `venv` folder removes everything cleanly — no leftover global pollution.

**What does activation do?**
Running `Activate.ps1` modifies your current terminal session's `PATH` environment variable. It prepends the `venv\Scripts\` directory to the front of PATH. This means when you type `python` or `pip`, your terminal finds the *venv's* versions first, not the system's. This change only affects the current terminal session — opening a new terminal window requires activation again.

**Why PowerShell specifically?**
Windows has multiple shells. PowerShell uses `.ps1` scripts for activation. If you use Command Prompt (CMD), use `.\venv\Scripts\activate.bat` instead. The result is identical.

**Possible problem — Execution Policy:**
PowerShell may refuse to run `.ps1` scripts by default due to its execution policy. If you see an error about this, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` and try again. This allows locally created scripts to run.

---

---

## STEP 2 — Install Dependencies and Freeze Requirements

### IMPLEMENT

With `(venv)` active in your terminal:

```bash
pip install opencv-python numpy
pip freeze > requirements.txt
```

Then create an empty file at `phase1_camera/__init__.py` (just create the file, leave it empty).

---

### UNDERSTAND

**What is `pip`?**
`pip` stands for "Pip Installs Packages." It is Python's official package manager. It connects to the **Python Package Index (PyPI)** — a public registry of over 500,000 open-source Python packages — downloads the requested package and all its dependencies, and installs them into the currently active environment's `site-packages` folder.

**What is `opencv-python`?**
OpenCV (Open Source Computer Vision Library) is a C++ library. `opencv-python` is a Python *binding* — a thin Python wrapper that exposes OpenCV's C++ functions to Python code. When you call `cv2.VideoCapture(0)` in Python, Python passes the call to the underlying C++ code, which executes at native speed. This is why OpenCV is fast despite being called from Python.

The importable name is `cv2` (not `opencv`). This is a historical naming quirk you must memorize.

**What is NumPy?**
NumPy (Numerical Python) provides the `ndarray` — an n-dimensional array stored as a contiguous block of memory. All image frames are NumPy arrays. OpenCV *depends on* NumPy, so `pip install opencv-python` often installs NumPy automatically — but listing it explicitly in your install command is best practice to make the dependency clear.

**What does `pip freeze` do?**
`pip freeze` lists every package currently installed in the active environment, along with its exact version number, in a format like `opencv-python==4.9.0.80`. Redirecting this output to `requirements.txt` with `>` saves it to a file.

**Why does `requirements.txt` matter?**
Anyone (including future you on a new machine) can recreate your exact environment by running `pip install -r requirements.txt`. The `-r` flag means "read from file." Without this file, there's no record of which library versions your project depends on.

**What is `__init__.py`?**
Python's import system only recognizes a folder as a *package* (importable collection of modules) if that folder contains a file named `__init__.py`. Without it, `from phase1_camera.camera_capture import ...` would fail with a `ModuleNotFoundError`. The file can be completely empty — its mere presence is the signal Python needs.

---

---

## STEP 3 — Open the Camera

### IMPLEMENT

In `phase1_camera/camera_capture.py`, write:

```python
import cv2

CAMERA_INDEX = 0

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    raise RuntimeError(f"Cannot open camera at index {CAMERA_INDEX}")
```

---

### UNDERSTAND

**What is `cv2.VideoCapture(index)`?**
This is the OpenCV function that opens a connection to a video capture device. Internally, on Windows, it calls into the **DirectShow** or **Media Foundation** multimedia API (depending on your OpenCV build). That API communicates with the camera's **device driver**, which sends a signal to the physical camera hardware to begin capturing frames.

The integer you pass is the **device index** — a number assigned by Windows to each recognized capture device, starting from `0`. Index `0` is almost always the first (or only) camera.

**What does it return?**
It returns a `VideoCapture` object — a handle to the open connection. Think of it exactly like a file handle from `open()`. It represents an ongoing, stateful resource. You must eventually close it (Step 9).

**What is `cap.isOpened()`?**
`VideoCapture(0)` does NOT raise an exception if it fails to open the camera. It silently returns a VideoCapture object that is in a "not opened" state. If you skip the `isOpened()` check and immediately try to read frames, you'll receive empty data with no explanation. `isOpened()` returns `True` only if the connection was successfully established.

**Why `raise RuntimeError`?**
Rather than printing a message and continuing (which would lead to confusing downstream errors), raising an exception immediately halts execution with a clear error message. `RuntimeError` is the appropriate built-in exception for a general runtime failure.

**What is `CAMERA_INDEX = 0`?**
This is a **constant** — a variable whose value is not meant to change. By convention, Python constants are named in `ALL_CAPS`. Storing the index as a named constant at the top of the file means that if you ever need to change it (e.g., you plug in a second camera), you change it in exactly one place. Never "hardcode" magic numbers inline.

**What is DirectShow?**
DirectShow is a Windows multimedia framework introduced in the late 1990s. It uses a pipeline of "filter" objects to process media data. USB webcams register themselves as DirectShow source filters, which means any application that knows how to talk to DirectShow can access them — including OpenCV. You never interact with DirectShow directly, but understanding it explains why camera index numbers exist and why some cameras may not respond as expected.

---

---

## STEP 4 — Read Camera Properties

### IMPLEMENT

Add this to `camera_capture.py`, after the `isOpened()` check:

```python
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps    = cap.get(cv2.CAP_PROP_FPS)

print(f"Camera opened: {width}x{height} @ {fps:.1f} FPS")
```

---

### UNDERSTAND

**What is `cap.get()`?**
The `VideoCapture` object stores a dictionary of properties about the capture session. `cap.get(property_id)` reads the current value of a specific property. All property IDs are defined as constants in the `cv2` module under the `CAP_PROP_*` namespace.

**What is `cv2.CAP_PROP_FRAME_WIDTH` and `CAP_PROP_FRAME_HEIGHT`?**
These are the pixel dimensions of each frame that the camera delivers. A standard webcam at default settings might report `640` wide and `480` tall. These values matter because every array operation you do on a frame depends on knowing its shape.

**What is `cv2.CAP_PROP_FPS`?**
FPS stands for **Frames Per Second** — how many frames the camera captures each second. A standard webcam runs at 30 FPS. This means it produces one new frame every `1/30 ≈ 33.3 milliseconds`. Understanding FPS is critical for later phases when you need to calculate speed of movement between frames.

**Why `int(cap.get(...))`?**
`cap.get()` always returns a `float` (e.g., `640.0`). For width and height, which are pixel counts and must be whole numbers, converting to `int` is necessary for correct use in array operations and function calls. FPS is left as a `float` because 29.97 FPS is a legitimate value.

**Why print this at startup?**
This is a **sanity check**. If your camera reports `0x0 @ 0.0 FPS`, the connection opened but the camera isn't delivering valid configuration data — a sign of a driver problem. Printing this at startup lets you catch the issue before the frame loop begins.

**What is an f-string?**
An f-string (formatted string literal) is a Python string prefixed with `f` that allows embedding expressions directly inside `{}`. `f"Camera opened: {width}x{height} @ {fps:.1f} FPS"` evaluates the variables inline. `:.1f` is a format specifier meaning: format as a float with 1 decimal place.

---

---

## STEP 5 — Define the Frame-Reading Function

### IMPLEMENT

Add this function to `camera_capture.py`:

```python
def read_frame(cap):
    success, frame = cap.read()
    return success, frame
```

---

### UNDERSTAND

**What is `cap.read()`?**
This is the core operation of the entire application. It requests one frame from the open camera connection. Under the hood, it:
1. Asks the OS API for the next buffered frame from the driver.
2. Decodes it (if needed).
3. Copies the pixel data into a newly allocated NumPy array.
4. Returns control to your code.

**What are the two return values?**
`cap.read()` returns a **tuple** of two values, which Python allows you to unpack directly with `success, frame = cap.read()`:
- `success` (bool): `True` if a frame was successfully read, `False` if not (e.g., camera disconnected mid-session).
- `frame` (numpy.ndarray or `None`): The pixel data of the frame if successful, or `None` if `success` is `False`.

**What is a NumPy ndarray?**
An `ndarray` (n-dimensional array) is the fundamental data structure in NumPy. For a color image frame, it has:
- **Shape:** `(height, width, 3)` — e.g., `(480, 640, 3)` for a 640×480 frame with 3 color channels.
- **dtype:** `uint8` — unsigned 8-bit integer. Each channel value is a whole number from `0` to `255`.
- **Memory layout:** Row-major (C-order) — pixel data is stored row by row in a single contiguous block of memory. The total size is `height × width × 3` bytes.

**What is BGR?**
OpenCV stores color images in **BGR** order — Blue channel first, then Green, then Red. This is the *opposite* of the more common RGB order used by most other systems. This convention came from early Windows multimedia APIs that delivered data in this format. OpenCV's own display functions (`imshow`) expect BGR input, so for Phase 1 you don't need to convert. But be aware: if you pass a frame to any non-OpenCV library, you likely need to flip the channel order.

**Why wrap `cap.read()` in a function?**
This is the **separation of concerns** principle. The `camera_capture.py` module is solely responsible for hardware interaction. `camera_app.py` (next steps) handles orchestration. By wrapping `cap.read()` in `read_frame()`, you create a clean interface. If you later switch from a local webcam to an IP camera or a video file, you only change `camera_capture.py` — the rest of your code remains untouched.

**Is `cap.read()` blocking?**
Yes. It does not return until the camera delivers the next frame. This is **synchronous I/O**. At 30 FPS, it blocks for approximately 33ms per call. This is actually what paces your main loop — you do not need to add any artificial `time.sleep()` delays. Adding sleep would cause your loop to run *slower* than the camera's frame rate, causing the driver's buffer to fill up with unconsumed frames, which manifests as video lag.

---

---

## STEP 6 — Create the Main Application File and Window

### IMPLEMENT

In `phase1_camera/camera_app.py`, write:

```python
import cv2
from phase1_camera.camera_capture import cap, read_frame, width, height, fps

WINDOW_NAME = "Human Tracking — Phase 1"

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, width, height)
```

---

### UNDERSTAND

**What is `import cv2`?**
The `import` statement loads a module into the current script's namespace. `cv2` is the OpenCV module. After this line, all OpenCV functions are accessible via `cv2.<function_name>`.

**What is `from phase1_camera.camera_capture import ...`?**
This uses Python's dot-notation import system to pull specific names from another module in your package. `phase1_camera` is the package (the folder with `__init__.py`), and `camera_capture` is the module (the `.py` file inside it). Importing `cap`, `read_frame`, `width`, `height`, `fps` makes them available in this file without needing to prefix them with the module name.

**What is `cv2.namedWindow(name, flag)`?**
This creates a GUI window managed by OpenCV's **HighGUI** subsystem. HighGUI is OpenCV's built-in, minimal GUI toolkit. It provides just enough functionality to display images and receive keyboard/mouse input.

- The `name` string is the window's unique identifier. All future calls to `imshow`, `resizeWindow`, `destroyWindow`, etc. reference this window by this exact string.
- The `flag` controls window behavior:
  - `cv2.WINDOW_AUTOSIZE`: The window size is fixed to the image size and cannot be manually resized.
  - `cv2.WINDOW_NORMAL`: The window can be freely resized by dragging its borders.

**Why `WINDOW_NORMAL` with an explicit `resizeWindow`?**
Using `WINDOW_NORMAL` lets you manually resize the window later. Then `cv2.resizeWindow(WINDOW_NAME, width, height)` sets the *initial* size to match the camera's reported frame dimensions. This ensures the window opens at the right size immediately rather than at some default.

**What is a named constant for the window name?**
`WINDOW_NAME = "Human Tracking — Phase 1"` is a constant. The window name is referenced in multiple places (`namedWindow`, `imshow`, `destroyWindow`). If it were hardcoded as a string in each place, a typo in one location would silently create a *second* window instead of operating on the existing one. With a constant, any typo is caught immediately as a `NameError`.

---

---

## STEP 7 — Write the Main Event Loop

### IMPLEMENT

Add this to `camera_app.py`, after the window creation:

```python
is_running = True

while is_running:
    success, frame = read_frame(cap)

    if not success:
        print("Frame read failed. Camera may have disconnected.")
        is_running = False
        continue

    cv2.imshow(WINDOW_NAME, frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        is_running = False
```

---

### UNDERSTAND

**What is `is_running = True`?**
This is a **state flag** — a boolean variable that represents the current running state of your application. Using a named flag instead of `while True:` + `break` makes your loop's termination logic explicit. Multiple exit conditions (key press, camera failure, etc.) all converge on setting `is_running = False`, which leads to a single, clean exit path.

**What is the `while` loop doing?**
The `while is_running:` loop is your application's **event loop** — the core control structure of any real-time application. Each iteration (one complete execution from top to bottom) corresponds to processing one frame of video. At 30 FPS, this loop body executes approximately 30 times per second.

**Why check `if not success`?**
`read_frame()` returns `(True, frame)` under normal conditions. But if the camera is physically disconnected mid-session, or if the driver encounters an error, it returns `(False, None)`. Attempting to call `cv2.imshow()` with a `None` frame would crash with an unreadable error. The `not success` check detects this, prints a human-readable message, and triggers a clean exit instead of a crash.

**What does `continue` do here?**
`continue` immediately jumps to the next iteration of the loop — skipping all remaining code below it in the current iteration. After setting `is_running = False` and calling `continue`, the loop condition is checked again (`is_running` is now `False`), and the loop exits cleanly without attempting `imshow` with a bad frame.

**What is `cv2.imshow(name, frame)`?**
`imshow` takes the NumPy array (`frame`) and places it into an internal display buffer associated with the named window. It does **not** immediately paint to the screen. The actual screen update happens only when `cv2.waitKey()` is called. This is a critical detail: calling `imshow` in a loop without `waitKey` will result in a frozen window.

**What is `cv2.waitKey(1)`?**
`waitKey(n)` does two things at once:
1. **Processes all pending GUI events** for all OpenCV windows (repaints, mouse input, window close events). Without this call every frame, your window would be completely unresponsive and frozen.
2. **Listens for a keyboard press** for `n` milliseconds. If a key is pressed, it returns the key's integer code. If no key is pressed within `n` ms, it returns `-1`.

The argument `1` means it waits at most 1 millisecond. This is short enough that it adds negligible delay to your loop, while still allowing the GUI to refresh every frame. Using `0` instead of `1` would make it block forever waiting for a keypress — your video would freeze.

**What is `& 0xFF`?**
`waitKey()` returns a 32-bit integer. On some platforms, modifier keys (Shift, Ctrl, etc.) set bits in the upper bytes of this integer. Performing a bitwise AND with `0xFF` (binary: `00000000 00000000 00000000 11111111`) masks out all but the lowest 8 bits, isolating the actual character code. This ensures cross-platform consistency.

**What is `ord('q')`?**
`ord()` returns the ASCII integer code for a character. `ord('q')` returns `113`. Comparing `key == ord('q')` is equivalent to `key == 113` but is far more readable. ASCII (American Standard Code for Information Interchange) is a 128-character encoding standard that assigns a unique integer to each printable character and control code.

---

---

## STEP 8 — Display FPS on the Frame (Optional but Recommended)

### IMPLEMENT

Add this block **between** the `if not success` block and `cv2.imshow()`:

```python
import time

prev_time = time.time()

# Inside the loop, before imshow:
curr_time = time.time()
loop_fps  = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
prev_time = curr_time

cv2.putText(
    frame,
    f"FPS: {loop_fps:.1f}",
    (10, 30),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.0,
    (0, 255, 0),
    2
)
```

---

### UNDERSTAND

**What is `time.time()`?**
`time.time()` returns the current time as a float representing **seconds since the Unix epoch** (January 1, 1970, 00:00:00 UTC). By recording the time at the start and end of each loop iteration, you can calculate how long one iteration took.

**How is live FPS calculated?**
`loop_fps = 1.0 / (curr_time - prev_time)` uses the formula: FPS = 1 / (seconds per frame). If one frame takes 0.033 seconds, that's `1/0.033 ≈ 30 FPS`. The `if (curr_time - prev_time) > 0` guard prevents a division-by-zero on the very first frame.

**What is `cv2.putText()`?**
`putText` draws a text string directly onto a NumPy array (your frame). The parameters in order are:
1. `frame` — the image to draw on (modified **in-place**).
2. `f"FPS: {loop_fps:.1f}"` — the text string.
3. `(10, 30)` — the (x, y) position in pixels of the **bottom-left corner** of the text. x=0 is the left edge, y=0 is the **top** edge (image coordinates are top-down, not bottom-up).
4. `cv2.FONT_HERSHEY_SIMPLEX` — the font. OpenCV has a small set of built-in fonts based on the Hershey font library. `SIMPLEX` is clean and readable.
5. `1.0` — font scale (size multiplier).
6. `(0, 255, 0)` — color in **BGR**: full green.
7. `2` — line thickness in pixels.

**Why does this go before `imshow` and not after?**
`imshow` copies the array to a display buffer but does not modify the original. Annotations drawn after `imshow` will not appear in the window for the current frame. Draw all overlays onto the frame *before* calling `imshow`.

**Why is this "in-place" modification significant?**
`putText` modifies the NumPy array directly in memory — it does not create a copy. This is efficient but means the original frame data is permanently altered. If you need the original clean frame for processing later in the same iteration (e.g., feeding it to a detection model in Phase 2), you must create a copy with `display_frame = frame.copy()` and draw on `display_frame` instead.

---

---

## STEP 9 — Release Resources on Exit

### IMPLEMENT

Wrap your entire camera opening and loop in a `try/finally` block. The final structure of `camera_app.py` should look like:

```python
import cv2
import time
from phase1_camera.camera_capture import read_frame, width, height

WINDOW_NAME = "Human Tracking — Phase 1"
CAMERA_INDEX = 0

try:
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera at index {CAMERA_INDEX}")

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, width, height)

    is_running = True
    prev_time  = time.time()

    while is_running:
        success, frame = cap.read()

        if not success:
            print("Frame read failed.")
            is_running = False
            continue

        curr_time  = time.time()
        loop_fps   = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time  = curr_time

        cv2.putText(frame, f"FPS: {loop_fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        cv2.imshow(WINDOW_NAME, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            is_running = False

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Camera released. Application closed.")
```

---

### UNDERSTAND

**What is `try/finally`?**
`try/finally` is a Python exception-handling construct that guarantees the `finally` block **always executes**, regardless of what happens inside `try` — whether the code completes normally, an exception is raised, the user presses Ctrl+C, or `break` is called. It is the correct mechanism for resource cleanup in Python.

**What is `cap.release()`?**
This closes the VideoCapture object's connection to the OS multimedia API, which in turn instructs the driver to stop capturing and signals to Windows that the hardware resource is no longer in use. After `release()`, the camera becomes available to other applications. If you skip this, the camera may remain "locked" to your (now-exited) Python process, making it inaccessible to other programs until you restart or kill the process.

**What is `cv2.destroyAllWindows()`?**
This closes every GUI window OpenCV has created in the current process and frees their memory. On some platforms, failing to call this can leave orphaned window handles or cause the process to hang at exit (the OS waiting for the GUI thread to clean up). Calling it explicitly ensures a clean exit every time.

**What is `KeyboardInterrupt`?**
When the user presses `Ctrl+C` in the terminal, the OS sends a SIGINT signal to the Python process. Python catches this and raises a `KeyboardInterrupt` exception. Because `KeyboardInterrupt` is also an exception, `finally` catches it and runs cleanup before the process terminates. This is why your camera will be released correctly even if the user force-stops the script.

**Why is `cap.release()` placed before `destroyAllWindows()`?**
The order matters: release the hardware resource first, then clean up the software GUI. Destroying windows first is not harmful, but releasing the camera while windows are still open can sometimes cause display artifacts on certain drivers.

**What is the overall data flow in this complete structure?**

```
[Physical Camera]
       ↓ USB hardware signal
[Windows OS Driver]
       ↓ DirectShow / Media Foundation API
[cv2.VideoCapture(0)]     ← opened in try block
       ↓ cap.read() called each frame
[NumPy ndarray (H×W×3, uint8, BGR)]
       ↓ putText draws overlay on array
[Annotated frame]
       ↓ cv2.imshow()
[HighGUI display buffer]
       ↓ cv2.waitKey(1) flushes buffer to screen
[Your monitor screen]
       ↓ keyboard event detected by waitKey
[Loop continues or exits]
       ↓ finally block
[cap.release() + destroyAllWindows()]
```

Every arrow in this chain is a concept you now understand.

---

---

## STEP 10 — Run the Application

### IMPLEMENT

With your virtual environment active, from your project root directory:

```bash
python -m phase1_camera.camera_app
```

---

### UNDERSTAND

**Why `python -m phase1_camera.camera_app` instead of `python camera_app.py`?**
Running with `-m` treats the argument as a **module path** relative to the current directory. This means Python adds the current directory to `sys.path` (the list of places Python looks for modules) and resolves the `from phase1_camera.camera_capture import ...` statement correctly.

If you `cd` into `phase1_camera/` and run `python camera_app.py` directly, the relative import will fail with `ModuleNotFoundError` because Python can't find the `phase1_camera` package — it's looking inside the folder, not above it.

**What is `sys.path`?**
`sys.path` is a Python list of directory paths that the interpreter searches when an `import` statement is encountered. When Python starts, it pre-populates `sys.path` with the script's directory, the virtual environment's `site-packages`, and a few standard library paths. Understanding `sys.path` is essential for resolving import errors.

---

---

## STEP 11 — Validation Checklist

Your Phase 1 application is complete when **every** item below passes:

| Check | How to Verify |
|---|---|
| Window opens immediately | Run the script — a window titled "Human Tracking — Phase 1" appears |
| Live video is displayed | You can see yourself (or the room) in the feed |
| Feed is smooth, no lag | Motion looks real-time, not delayed or choppy |
| FPS counter is visible | Green FPS text appears in the top-left of the window |
| `Q` key exits cleanly | Press `Q` — window closes, terminal prints "Camera released" |
| No exceptions in terminal | Terminal output shows only your print statements, no tracebacks |
| Camera re-opens immediately | Run the script again right away — it opens without error |
| 5-minute stress test passes | Leave running for 5 minutes — no memory growth, no lag increase |

---

---

## Key Concepts Quick Reference

| Concept | One-Line Summary |
|---|---|
| `VideoCapture(index)` | Opens a connection to a camera device by index number |
| `cap.read()` | Blocking call that retrieves one frame as a NumPy array |
| `ndarray shape (H, W, 3)` | Frame dimensions: rows × columns × color channels |
| `dtype uint8` | Each pixel channel is a value from 0 to 255 |
| BGR color order | OpenCV's channel order — Blue first, then Green, then Red |
| `imshow` | Puts frame into display buffer — does NOT update screen |
| `waitKey(1)` | Flushes display buffer to screen AND polls for keyboard input |
| `& 0xFF` | Masks key code to lower 8 bits for cross-platform correctness |
| `ord('q')` | Converts character to ASCII integer for key comparison |
| `is_running` flag | Boolean state controlling loop continuation |
| `try/finally` | Guarantees cleanup code (release, destroyAllWindows) always runs |
| `cap.release()` | Returns camera hardware to the OS — must always be called |
| `python -m module` | Runs module with correct `sys.path` for relative imports |
| `pip freeze` | Saves exact installed package versions to `requirements.txt` |

---

*Version 2.0 — Human Tracking System, Phase 1*
*Format: Implementation-first with embedded conceptual depth*
