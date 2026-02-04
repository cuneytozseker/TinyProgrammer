python
import time
import random
import math
from tiny_canvas import Canvas

# Importing necessary libraries
from tiny_canvas import Canvas

# Initializing the canvas
c = Canvas()

def draw_spiral(r, g, b):
    """
    Draws an expanding spiral pattern on the canvas.
    
    :param r: Red component of color (0-255)
    :param g: Green component of color (0-255)
    :param b: Blue component of color (0-255)
    """
    # Clearing the canvas
    c.clear(r, g, b)
    
    # Setting up variables for the spiral pattern
    x, y = 100, 100
    radius = 30
    
    # Main loop to draw the spiral
    while True:
        # Drawing a large circle at the center of the canvas
        c.fill_circle(x, y, radius, r, g, b)
        
        # Moving the circle outward
        x += 1
        if abs(x - radius) > 20:  # If the circle moves outside the canvas
            x = 0
        
        # Reducing the radius of the circle for a spiral effect
        radius -= 0.5
    
    return

# Call the function to draw the spiral pattern
draw_spiral(0, 0, 255)
