"""
Shared frame buffer for MJPEG web streaming.

Terminal pushes JPEG frames here after each render; the Flask
/stream endpoint reads them to serve a live browser preview.
"""

import io
import threading

_lock = threading.Lock()
_latest_frame: bytes = b""


def put_frame(surface) -> None:
    """Convert a pygame surface to JPEG and store it for streaming."""
    global _latest_frame
    try:
        import numpy as np
        from PIL import Image

        # surfarray gives (w, h, 3); PIL wants (h, w, 3)
        arr = __import__('pygame').surfarray.array3d(surface)
        arr = arr.transpose(1, 0, 2)
        img = Image.fromarray(arr.astype("uint8"), "RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        frame = buf.getvalue()

        with _lock:
            _latest_frame = frame
    except Exception:
        pass


def get_frame() -> bytes:
    """Return the latest JPEG frame bytes (empty if none yet)."""
    with _lock:
        return _latest_frame
