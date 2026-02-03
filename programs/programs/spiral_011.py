python
import time
import random
import math

# Importing the necessary library for drawing
from tiny_canvas import Canvas

c = Canvas(480, 320)

while True:
    # Drawing a spiral pattern
    c.clear()
    
    # Starting from the center of the canvas
    x, y = (c.width // 2), (c.height // 2)
    
    # Rotating by 90 degrees
    for _ in range(360):
        r = math.cos(_ * math.pi / 180)
        g = math.sin(_ * math.pi / 180)
        
        # Drawing the spiral pattern
        c.fill_circle(x, y, 50, r, g, b)
    
    # Adding some delay to make the pattern visible
    time.sleep(0.1)

# Clearing up resources when done
c.clear()
