"""
Direct Framebuffer Writer for SPI TFT Displays

Bypasses SDL's broken fbcon driver on Bookworm/Trixie by:
1. Rendering to an in-memory pygame surface
2. Converting to RGB565 and writing directly to /dev/fb0

Works with fbtft-based displays (ILI9486, ILI9341, etc.)
Also works with HDMI displays that report portrait framebuffer (480x800)
"""

import os
import numpy as np

from .color_adjustment import apply_color_adjustment

# Module-level color scheme setting (can be changed at runtime)
_color_scheme = "none"


def set_color_scheme(scheme_name: str):
    """Set the active color scheme for framebuffer output."""
    global _color_scheme
    _color_scheme = scheme_name
    print(f"[FB] Color scheme set to: {scheme_name}")


def get_color_scheme() -> str:
    """Get the current color scheme name."""
    return _color_scheme


# Check if we're on a system with a framebuffer
FB_DEVICE = os.environ.get("FB_DEVICE", "/dev/fb0")
IS_FRAMEBUFFER_AVAILABLE = os.path.exists(FB_DEVICE)

# Rotation setting: 0=none, 1=90°CW, 2=180°, 3=270°CW (90°CCW)
# Set via environment variable or auto-detect based on framebuffer dimensions
FB_ROTATION = int(os.environ.get("FB_ROTATION", "-1"))  # -1 = auto-detect


def rgb888_to_rgb565(surface) -> np.ndarray:
    """
    Convert a pygame surface (RGB888) to RGB565 numpy array.
    Applies color adjustment layer if set.

    RGB565 format: RRRRR GGGGGG BBBBB (16 bits)
    """
    import pygame
    # Get pixel array (RGB888)
    arr = pygame.surfarray.array3d(surface)  # Shape: (width, height, 3)

    # Extract RGB channels
    r = arr[:, :, 0].astype(np.uint16)
    g = arr[:, :, 1].astype(np.uint16)
    b = arr[:, :, 2].astype(np.uint16)

    # Apply color adjustment layer if active
    if _color_scheme != "none":
        r, g, b = apply_color_adjustment(r, g, b, _color_scheme)

    # Convert to RGB565
    # R: 8 bits -> 5 bits (shift right 3, then left 11)
    # G: 8 bits -> 6 bits (shift right 2, then left 5)
    # B: 8 bits -> 5 bits (shift right 3)
    rgb565 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

    # Transpose because pygame uses (x, y) but framebuffer uses (y, x)
    return rgb565.T.astype(np.uint16)


class FramebufferWriter:
    """
    Writes pygame surfaces directly to a Linux framebuffer device.
    Supports rotation for displays with portrait-mode framebuffers.
    """

    def __init__(self, width: int = 480, height: int = 320, device: str = None):
        self.render_width = width   # What we render at (landscape)
        self.render_height = height
        self.device = device or FB_DEVICE
        self.enabled = IS_FRAMEBUFFER_AVAILABLE
        self.rotation = FB_ROTATION
        self.fb_width = width
        self.fb_height = height

        if self.enabled:
            # Get actual framebuffer dimensions
            try:
                size_path = f"/sys/class/graphics/{os.path.basename(self.device)}/virtual_size"
                if os.path.exists(size_path):
                    with open(size_path) as f:
                        self.fb_width, self.fb_height = map(int, f.read().strip().split(','))

                        # Auto-detect rotation if framebuffer is portrait but we render landscape
                        if self.rotation == -1:
                            if self.fb_width < self.fb_height and width > height:
                                # Framebuffer is portrait, we render landscape - need 270° CW (90° CCW) rotation
                                self.rotation = 3
                                print(f"[FB] Auto-detected rotation: 270° CW (portrait FB {self.fb_width}x{self.fb_height} -> landscape {width}x{height})")
                            else:
                                self.rotation = 0

                        if self.rotation == 0 and (self.fb_width != width or self.fb_height != height):
                            print(f"[FB] Warning: Expected {width}x{height}, got {self.fb_width}x{self.fb_height}")
            except Exception as e:
                print(f"[FB] Could not verify dimensions: {e}")
                self.rotation = 0 if self.rotation == -1 else self.rotation

    def write(self, surface) -> bool:
        """
        Write a pygame surface to the framebuffer.
        Handles rotation if framebuffer orientation differs from render orientation.
        Returns True on success, False on failure.
        """
        if not self.enabled:
            return False

        try:
            # Convert to RGB565
            rgb565 = rgb888_to_rgb565(surface)

            # Apply rotation if needed
            if self.rotation == 1:  # 90° CW
                rgb565 = np.rot90(rgb565, k=-1)  # k=-1 is 90° CW
            elif self.rotation == 2:  # 180°
                rgb565 = np.rot90(rgb565, k=2)
            elif self.rotation == 3:  # 270° CW (90° CCW)
                rgb565 = np.rot90(rgb565, k=1)  # k=1 is 90° CCW

            # Ensure contiguous array for writing
            rgb565 = np.ascontiguousarray(rgb565)

            # Write to framebuffer
            with open(self.device, 'r+b') as fb:
                fb.write(rgb565.tobytes())

            return True
        except Exception as e:
            print(f"[FB] Write error: {e}")
            return False

    def clear(self, r: int = 0, g: int = 0, b: int = 0) -> bool:
        """
        Clear the framebuffer with a solid color.
        """
        if not self.enabled:
            return False

        try:
            # Convert RGB888 to RGB565
            color = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            data = np.full((self.height, self.width), color, dtype=np.uint16)

            with open(self.device, 'r+b') as fb:
                fb.write(data.tobytes())

            return True
        except Exception as e:
            print(f"[FB] Clear error: {e}")
            return False


# Singleton instance for easy access
_writer = None

def get_writer(width: int = 480, height: int = 320) -> FramebufferWriter:
    """Get or create the global framebuffer writer."""
    global _writer
    if _writer is None:
        _writer = FramebufferWriter(width, height)
    return _writer
