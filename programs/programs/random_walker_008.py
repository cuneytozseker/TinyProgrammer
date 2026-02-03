python
import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()

def animate_dot():
    # Generate a random x and y coordinates within the canvas
    x = random.randint(0, c.width)
    y = random.randint(0, c.height)
    
    # Calculate the dot's radius (assuming it's a simple circle)
    radius = 5
    
    # Fill the circle with random colors
    c.fill_circle(x, y, radius, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    # Update the display
    c.update()

while True:
    animate_dot()
    time.sleep(1)
