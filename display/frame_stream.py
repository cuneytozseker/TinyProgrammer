"""
Shared frame buffer for MJPEG web streaming.

Terminal pushes frames here after each render; the Flask /stream endpoint
reads them to serve a live browser preview.

Encoding is rate-limited to ~10fps so the overhead on slow hardware
(Pi Zero, Pi 4) is negligible regardless of the display refresh rate.
"""

import io
import time
import threading

_lock = threading.Lock()
_latest_frame: bytes = b""
_last_encode_time: float = 0.0
_ENCODE_INTERVAL = 0.1  # seconds — caps encoding at ~10fps


def put_frame(surface) -> None:
    """Convert a pygame surface to JPEG and store it for streaming.

    Rate-limited: skips encoding if called more frequently than
    _ENCODE_INTERVAL, so fast render loops on the Pi pay almost no cost.
    """
    global _latest_frame, _last_encode_time

    now = time.monotonic()
    if now - _last_encode_time < _ENCODE_INTERVAL:
        return  # not time yet — skip encoding entirely

    try:
        import numpy as np
        from PIL import Image
        import pygame

        # surfarray gives (w, h, 3); PIL wants (h, w, 3)
        arr = pygame.surfarray.array3d(surface)
        arr = arr.transpose(1, 0, 2)
        img = Image.fromarray(arr.astype("uint8"), "RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        frame = buf.getvalue()

        with _lock:
            _latest_frame = frame
        _last_encode_time = now
    except Exception:
        pass


def get_frame() -> bytes:
    """Return the latest JPEG frame bytes (empty bytes if none yet)."""
    with _lock:
        return _latest_frame
