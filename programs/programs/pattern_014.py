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

# Initialize the canvas
c = Canvas()

def draw_pattern():
    r, g, b = 255, 0, 0  # Set initial color to red
    for _ in range(10):  # Draw a pattern for 10 iterations
        c.fill_rect(random.randint(0, c.width), random.randint(0, c.height), 10, 10, r, g, b)
        time.sleep(0.5)  # Wait for 0.5 seconds

# Run the infinite loop
while True:
    draw_pattern()
