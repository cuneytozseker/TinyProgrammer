python
import time
import random
import math

from tiny_canvas import Canvas

def animate_dot():
    """Animate a dot randomly walking around the screen."""
    while True:
        # Generate random x and y coordinates within the canvas boundaries
        x = min(c.width, max(0, random.uniform(0, c.width)))
        y = min(c.height, max(0, random.uniform(0, c.height)))
        
        # Draw the dot with a random color
        c.fill_circle(x, y, 10, 255, 0, 0, 255)
        
        # Wait for a short time before drawing again
        time.sleep(0.1)

# Create an instance of Canvas and start the animation
c = Canvas()
animate_dot()
