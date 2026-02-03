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

def animate_dot():
    while True:
        # Get a random x and y coordinates
        x = random.randint(0, c.width)
        y = random.randint(0, c.height)
        
        # Draw the dot at the random position
        c.fill_rect(x, y, 10, 10, 255, 255, 255)
        
        # Sleep for a short duration to see the change
        time.sleep(0.1)

# Run the animation loop indefinitely
animate_dot()
