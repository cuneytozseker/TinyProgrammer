python
import time
import random
import math
from tiny_canvas import Canvas

# Initialize variables
c = Canvas(480, 320)
width, height = c.width, c.height

# Define the spiral size and speed
spiral_size = 10
speed = 5

while True:
    # Clear the canvas
    c.clear(0, 0, 0)  # RGB values are black in this example
    
    # Increase the spiral size with each iteration
    spiral_size += 1

    # Calculate the radius of the circle based on the current spiral size
    circle_radius = spiral_size / 5 + 2

    # Fill the circle at its center
    c.fill_circle(width // 2, height // 2, circle_radius)

    # Add a small delay to mimic movement
    time.sleep(speed)
