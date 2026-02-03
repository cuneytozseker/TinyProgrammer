python
import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()

def create_ascii_animation():
    while True:
        # Clear the canvas with white background
        c.clear(255, 255, 255)
        
        # Draw a small rectangle on the canvas
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        c.fill_rect(10, 10, 40, 30, r, g, b)
        
        # Sleep for a short duration
        time.sleep(1)

create_ascii_animation()
