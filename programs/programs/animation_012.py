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

def animate():
    while True:
        # Clear the screen with black background
        c.clear(0, 0, 0)
        
        # Draw a circle at the center of the canvas with radius 50
        c.fill_circle(c.width // 2, c.height // 2, 50, 255, 255, 255)
        
        # Wait for 1 second
        time.sleep(1)

# Start the animation loop
animate()
