python
import time
import random
import math
from tiny_canvas import Canvas

# Initial setup (not required for this simple example)
canvas = Canvas(480, 320)

while True:
    # Clear the canvas
    c.clear(255, 255, 255)  # White background

    # Generate random points on the canvas
    for _ in range(100):
        x = random.randint(0, 480)
        y = random.randint(0, 320)
        c.fill_circle(x, y, 10, (random.random(), random.random(), random.random()))

    # Sleep for a short period to see the effect
    time.sleep(0.5)

    # Refresh the canvas after some delay (e.g., every second)
    canvas.refresh()
