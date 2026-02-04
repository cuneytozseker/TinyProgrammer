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
c.clear(0, 0, 255)  # Fill the canvas with white
time.sleep(1)  # Wait for 1 second
c.fill_rect(100, 100, 200, 50, 0, 255, 255)  # Draw a circle at (100, 100) with radius 50

# Infinite loop to display the clock
while True:
    # Calculate the current time in seconds since the epoch
    current_time = time.time()
    
    # Update the position of the circle based on the current time
    x = 100 + int(math.cos(current_time * math.pi / 3))
    y = 100 + int(math.sin(current_time * math.pi / 3))
    
    # Fill the circle at its new position
    c.fill_circle(x, y, 50, 255, 255, 255)
    
    # Wait for 1 second before moving to the next position
    time.sleep(1)
