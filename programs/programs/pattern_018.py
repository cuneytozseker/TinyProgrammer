python
import time
import random
import math

from tiny_canvas import Canvas

c = Canvas()

def generate_pattern(r, g, b):
    """
    Generates a mesmerizing repeating pattern on the canvas.
    Parameters:
    - r (int): Red component of the color.
    - g (int): Green component of the color.
    - b (int): Blue component of the color.

    The pattern is a simple star pattern filled with the specified colors.
    """
    width, height = c.width, c.height
    for x in range(width):
        y = int(height / 2)
        for i in range(1, 360):
            angle = math.radians(i * (3.14 / 180))  # Convert degrees to radians
            r_x = r + cos(angle) * width
            g_y = g + sin(angle) * height
            c.draw_polygon((x, y), (r_x, g_y), (b, b))
```

This corrected version of the function now uses the `draw_polygon` method instead of `fill_rect`, ensuring that the pattern is filled with the specified colors.