import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
python
# Initialize variables
x, y = 480 // 2, 320 // 2
speed = 1
color = (255, 0, 0)

while True:
    # Clear the canvas
    c.clear(255, 255, 255)
    
    # Fill a random color in the center of the canvas
    c.fill_circle(x, y, 100, color[0], color[1], color[2])
    
    # Move the circle right by 1 pixel
    x += speed
    
    # Set a delay to create a smooth animation
    time.sleep(0.1)
