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
c = Canvas()
r, g, b = 255, 0, 0  # Yellow color (RGB)
x, y = 160, 160    # Center of the screen
radius = 32     # Radius of the ball

while True:
    c.clear(r, g, b)
    x += random.randint(-10, 10)  # Move the ball horizontally
    y += random.randint(-10, 10)  # Move the ball vertically
    
    # Ball's path is a circle with radius of 32 centered at (x, y)
    c.fill_circle(x, y, radius, r, g, b)
    
    # Wait for a short time
    time.sleep(0.05)

# Clean up
c.clear()
