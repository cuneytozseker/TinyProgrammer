import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
python
# Initialize the canvas
canvas = Canvas()

def draw_pattern():
    while True:
        # Clear the canvas
        c.clear(255, 0, 0)  # Red for white background
        
        # Draw a repeating pattern
        # Example: A checkerboard pattern with random color and speed
        for i in range(10):
            x = i * 32
            y = i * 32
            c.fill_rect(x, y, 32, 32, random.randint(0, 255), random.randint(0, 255))
        
        # Sleep for a short time
        time.sleep(1)
    
# Run the pattern generation loop
draw_pattern()
