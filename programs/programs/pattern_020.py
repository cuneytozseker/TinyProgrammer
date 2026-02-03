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

def generate_pattern():
    while True:
        c.fill_rect(0, 0, 480, 320)
        # Generate random positions for circles and fill them
        for _ in range(10):
            x = random.randint(0, 480)
            y = random.randint(0, 320)
            r = random.randint(5, 25)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            c.fill_circle(x, y, r, g, b)
            # Wait for a short time to create the pattern
            time.sleep(0.1)

# Run the loop
generate_pattern()
