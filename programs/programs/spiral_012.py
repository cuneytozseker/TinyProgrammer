python
import time
import random
import math
from tiny_canvas import Canvas

# Initialize canvas
c = Canvas()

def draw_spiral():
    # Constants for the spiral's pattern
    radius = 200
    start_angle = 180
    step_angle = 6  # Adjust to change the speed of the spiral
    
    while True:
        # Clear the canvas
        c.clear(0, 0, 0)
        
        # Draw the spiral pattern
        for x in range(radius):
            y = radius - (x * step_angle)
            c.fill_circle(x, y, radius, 255, 0, 0, 255)
        
        # Wait for a short time to make the pattern move
        time.sleep(1)

# Run the spiral pattern
draw_spiral()
