import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
python
def draw_pattern():
    # Clear the canvas to start with a new pattern
    c.clear(0, 0, 0)

    # Define colors for different sections of the pattern
    colors = {
        'top': (255, 255, 255),  # White
        'middle': (200, 200, 200),  # Light Gray
        'bottom': (0, 0, 0)       # Black
    }

    # Define the size of each section of the pattern
    width = c.width // 3
    height = c.height // 3

    # Draw each section of the pattern
    for i in range(12):
        x, y = (i * width, i * height)
        c.fill_rect(x, y, width, height, colors['top'], colors['middle'], colors['bottom'])

# Run the infinite loop to continuously draw the pattern
while True:
    draw_pattern()
    time.sleep(0.1)  # Wait for a short duration before drawing again
