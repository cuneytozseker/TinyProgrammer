"""
Direct Framebuffer Writer for SPI TFT Displays

Bypasses SDL's broken fbcon driver on Bookworm/Trixie by:
1. Rendering to an in-memory pygame surface
2. Converting to RGB565 and writing directly to /dev/fb0

Works with fbtft-based displays (ILI9486, ILI9341, etc.)
"""

import os
import numpy as np

# Check if we're on a system with a framebuffer
FB_DEVICE = os.environ.get("FB_DEVICE", "/dev/fb0")
IS_FRAMEBUFFER_AVAILABLE = os.path.exists(FB_DEVICE)


def rgb888_to_rgb565(surface) -> np.ndarray:
    """
    Convert a pygame surface (RGB888) to RGB565 numpy array.

    RGB565 format: RRRRR GGGGGG BBBBB (16 bits)
    """
    import pygame
    # Get pixel array (RGB888)
    arr = pygame.surfarray.array3d(surface)  # Shape: (width, height, 3)

    # Extract RGB channels
    r = arr[:, :, 0].astype(np.uint16)
    g = arr[:, :, 1].astype(np.uint16)
    b = arr[:, :, 2].astype(np.uint16)

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
    """

    def __init__(self, width: int = 480, height: int = 320, device: str = None):
        self.width = width
        self.height = height
        self.device = device or FB_DEVICE
        self.enabled = IS_FRAMEBUFFER_AVAILABLE

        if self.enabled:
            # Verify framebuffer dimensions match
            try:
                size_path = f"/sys/class/graphics/{os.path.basename(self.device)}/virtual_size"
                if os.path.exists(size_path):
                    with open(size_path) as f:
                        fb_w, fb_h = map(int, f.read().strip().split(','))
                        if fb_w != width or fb_h != height:
                            print(f"[FB] Warning: Expected {width}x{height}, got {fb_w}x{fb_h}")
                            self.width = fb_w
                            self.height = fb_h
            except Exception as e:
                print(f"[FB] Could not verify dimensions: {e}")

    def write(self, surface) -> bool:
        """
        Write a pygame surface to the framebuffer.
        Returns True on success, False on failure.
        """
        if not self.enabled:
            return False

        try:
            # Convert to RGB565
            rgb565 = rgb888_to_rgb565(surface)

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
