import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
python
# Import necessary libraries
import time
import random
import math
from tiny_canvas import Canvas

# Initialize the canvas
c = Canvas()

# Define the number of spirals to draw
num_spirals = 50

# Define the size and color for each spiral
spiral_size = 100
circle_color = (255, 0, 0)

# Define the starting point for each spiral
start_point_x = c.width / 2
start_point_y = c.height / 2

# Define the direction of each spiral
direction_x = random.choice([-1, 1])
direction_y = random.choice([-1, 1])

# Draw a spiral pattern
for _ in range(num_spirals):
    x, y = start_point_x, start_point_y
    c.fill_rect(x, y, spiral_size, spiral_size, circle_color, circle_color)
    
    # Calculate the next point for the spiral
    new_x = x + direction_x * spiral_size
    new_y = y + direction_y * spiral_size
    
    # Check if we've drawn past the canvas boundaries or reached the same point
    if (new_x < 0 or new_y < 0) or (new_x >= c.width or new_y >= c.height):
        break
    
    # Change the direction of the next spiral
    if random.random() < 0.5:
        direction_x *= -1
    else:
        direction_y *= -1

# Wait a few seconds before drawing the next spiral
time.sleep(2)
