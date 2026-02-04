python
import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()

def draw_pattern():
    # Define colors and sizes for the pattern
    colors = ['red', 'blue', 'green', 'yellow']
    size = 10

    # Clear the canvas to start a new pattern
    c.clear(0, 0, 255)  # White background

    # Loop through each color in the list
    for i in range(len(colors)):
        # Fill the pattern with the current color
        c.fill_rect(random.randint(1, c.width - size), random.randint(1, c.height - size), size, size, colors[i], colors[i], colors[i])

# Run an infinite loop to draw the pattern
while True:
    draw_pattern()
    time.sleep(0.5)  # Adjust the sleep time as needed
