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

def draw_pattern():
    while True:
        # Clear the canvas
        c.clear(0, 0, 255)
        
        # Generate random colors
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        
        # Draw the pattern
        c.fill_rect(50, 50, 100, 100, r, g, b)
        
        # Sleep for a short time
        time.sleep(0.2)

# Run the function
draw_pattern()
