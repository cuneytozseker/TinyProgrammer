python
import time
import random
import math
from tiny_canvas import Canvas

# Initialize canvas and variables
c = Canvas()
canvas.width, canvas.height = 480, 320
x, y = c.width // 2, c.height // 2
angle = 0
radius = 50
speed = 10

while True:
    c.fill(0, 0, 0)  # Clear the canvas
    c.stroke(0)  # Set stroke color to black
    
    while y >= 0:
        x += math.cos(angle)
        y -= math.sin(angle)
        if (x ** 2 + y ** 2) > radius:
            break
        c.point((int(x), int(y)))
    
    # Increase the angle by a small increment
    angle += speed
    
    # Wait for a second to see the effect
    time.sleep(1)
