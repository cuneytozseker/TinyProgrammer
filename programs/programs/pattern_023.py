import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
python
import time
import random
import math
from tiny_canvas import Canvas

# Initialize variables before the loop
x, y = 0, 0
speed = 5
color_r = 255
color_g = 255
color_b = 255

while True:
    # Move the object in a random direction
    x += random.choice([-1, 1])
    y += random.choice([-1, 1])
    
    # Fill the circle at the new position with a random color
    c.fill_circle(x, y, 20, color_r, color_g, color_b)
    
    # Wait for a short time to simulate movement
    time.sleep(speed)
