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

# Define a function to generate random coordinates
def get_random_coordinates():
    return (random.randint(0, c.width - 1), random.randint(0, c.height - 1))

# Main loop for animation
while True:
    # Get a random coordinate
    x, y = get_random_coordinates()
    
    # Fill the rectangle with random color
    c.fill_rect(x, y, 20, 20, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    # Sleep for a short time
    time.sleep(1)
