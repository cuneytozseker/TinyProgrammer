"""
Color Adjustment Layer for TinyProgrammer Display

Applies Photoshop-style color adjustments to the entire rendered frame
before writing to framebuffer. Works on numpy arrays for efficiency.
"""

import numpy as np

# Preset color schemes
# Each scheme has: mode, color (RGB), intensity (0.0-1.0)
COLOR_SCHEMES = {
    "none": None,
    "amber": {"mode": "multiply", "color": (255, 191, 0), "intensity": 0.35},
    "green": {"mode": "multiply", "color": (0, 255, 100), "intensity": 0.3},
    "blue": {"mode": "multiply", "color": (100, 150, 255), "intensity": 0.25},
    "sepia": {"mode": "multiply", "color": (255, 220, 180), "intensity": 0.4},
    "cool": {"mode": "multiply", "color": (200, 220, 255), "intensity": 0.2},
    "warm": {"mode": "multiply", "color": (255, 230, 200), "intensity": 0.25},
    "night": {"mode": "multiply", "color": (255, 80, 80), "intensity": 0.4},
}


def apply_color_adjustment(r, g, b, scheme_name):
    """
    Apply color adjustment to RGB numpy arrays.

    Args:
        r, g, b: numpy arrays of uint16 for each color channel
        scheme_name: name of the color scheme to apply

    Returns:
        Tuple of (r, g, b) adjusted numpy arrays
    """
    if scheme_name == "none" or scheme_name not in COLOR_SCHEMES:
        return r, g, b

    scheme = COLOR_SCHEMES[scheme_name]
    if scheme is None:
        return r, g, b

    mode = scheme["mode"]
    color = scheme["color"]
    intensity = scheme["intensity"]

    if mode == "multiply":
        return apply_multiply(r, g, b, color, intensity)
    elif mode == "screen":
        return apply_screen(r, g, b, color, intensity)
    elif mode == "overlay":
        return apply_overlay(r, g, b, color, intensity)

    return r, g, b


def apply_multiply(r, g, b, color, intensity):
    """
    Multiply blend - tints/darkens the image.

    Formula: output = input * color / 255
    Then blend with original based on intensity.
    """
    cr, cg, cb = color

    # Calculate multiplied values
    r_mult = (r.astype(np.float32) * cr / 255.0)
    g_mult = (g.astype(np.float32) * cg / 255.0)
    b_mult = (b.astype(np.float32) * cb / 255.0)

    # Blend between original and multiplied based on intensity
    r_out = np.clip(r * (1 - intensity) + r_mult * intensity, 0, 255).astype(np.uint16)
    g_out = np.clip(g * (1 - intensity) + g_mult * intensity, 0, 255).astype(np.uint16)
    b_out = np.clip(b * (1 - intensity) + b_mult * intensity, 0, 255).astype(np.uint16)

    return r_out, g_out, b_out


def apply_screen(r, g, b, color, intensity):
    """
    Screen blend - lightens the image.

    Formula: output = 255 - ((255 - input) * (255 - color)) / 255
    """
    cr, cg, cb = color

    # Calculate screened values
    r_scr = 255 - ((255 - r.astype(np.float32)) * (255 - cr) / 255.0)
    g_scr = 255 - ((255 - g.astype(np.float32)) * (255 - cg) / 255.0)
    b_scr = 255 - ((255 - b.astype(np.float32)) * (255 - cb) / 255.0)

    # Blend with original
    r_out = np.clip(r * (1 - intensity) + r_scr * intensity, 0, 255).astype(np.uint16)
    g_out = np.clip(g * (1 - intensity) + g_scr * intensity, 0, 255).astype(np.uint16)
    b_out = np.clip(b * (1 - intensity) + b_scr * intensity, 0, 255).astype(np.uint16)

    return r_out, g_out, b_out


def apply_overlay(r, g, b, color, intensity):
    """
    Overlay blend - increases contrast while tinting.

    Formula: if input < 128: 2 * input * color / 255
             else: 255 - 2 * (255 - input) * (255 - color) / 255
    """
    cr, cg, cb = color

    def overlay_channel(ch, c):
        ch_f = ch.astype(np.float32)
        # Overlay formula
        result = np.where(
            ch_f < 128,
            2 * ch_f * c / 255.0,
            255 - 2 * (255 - ch_f) * (255 - c) / 255.0
        )
        return result

    r_ovl = overlay_channel(r, cr)
    g_ovl = overlay_channel(g, cg)
    b_ovl = overlay_channel(b, cb)

    # Blend with original
    r_out = np.clip(r * (1 - intensity) + r_ovl * intensity, 0, 255).astype(np.uint16)
    g_out = np.clip(g * (1 - intensity) + g_ovl * intensity, 0, 255).astype(np.uint16)
    b_out = np.clip(b * (1 - intensity) + b_ovl * intensity, 0, 255).astype(np.uint16)

    return r_out, g_out, b_out


def get_available_schemes():
    """Return list of available color scheme names."""
    return list(COLOR_SCHEMES.keys())
