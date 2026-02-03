import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
python
# Importing necessary libraries
import time
import random
import math
from tiny_canvas import Canvas

def animate_ball():
    while True:
        # Clear the canvas to draw a new ball
        c.clear(0, 255, 255)  # Blue background
        
        # Generate random coordinates for the ball
        x = random.randint(c.width // 4, c.width - c.width // 4)
        y = random.randint(c.height // 4, c.height - c.height // 4)
        
        # Determine the radius of the ball (5 pixels)
        radius = 5
        
        # Fill the circle with a random color
        c.fill_circle(x, y, radius, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # Wait for 1 second before drawing again
        time.sleep(1)

# Start the animation loop
animate_ball()
