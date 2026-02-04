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

# Initialize the canvas (480x320)
c = Canvas()

def draw_circle(x, y, radius, r, g, b):
    c.fill_circle(x, y, radius, r, g, b)

def main():
    while True:
        # Generate random positions and sizes for the circle
        x = random.randint(1, 480)
        y = random.randint(1, 320)
        radius = random.randint(15, 150)  # Adjusted size for more circles

        # Fill a small circle at the center of the canvas
        c.fill_circle(x, y, radius)

        # Randomly change color and speed
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        time.sleep(random.uniform(0.1, 0.3))

