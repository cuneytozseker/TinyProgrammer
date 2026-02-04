python
import time
import random
import math
from tiny_canvas import Canvas

# Initializing the canvas
c = Canvas()

def animate_dot():
    # Clear the screen
    c.clear(0, 0, 255)
    
    while True:
        # Randomly select a dot to move
        x = random.randint(0, c.width - 1)
        y = random.randint(0, c.height - 1)
        
        # Fill the dot with red color
        c.fill_circle(x, y, 25, 255, 0, 0, 255)
        
        # Wait for a short interval before moving again
        time.sleep(0.1)

# Running the animation
animate_dot()
