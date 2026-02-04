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
seconds = 0
x, y = c.width // 2, c.height // 2
radius = c.width // 4
color = (100, 100, 255)

while True:
    # Update the position of the circle
    x += math.cos(seconds * 3.14 / 60)
    y += math.sin(seconds * 3.14 / 60)

    # Fill the circle with a random color each second
    c.fill_circle(x, y, radius, color)

    # Clear the canvas after one second
    c.clear(255, 255, 255)
    
    # Wait for 1 second before updating the position of the circle again
    time.sleep(1)

    # Increment the seconds counter
    seconds += 1
