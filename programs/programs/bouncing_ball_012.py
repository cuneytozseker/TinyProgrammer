python
import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()

def draw_ball(c, x, y):
    c.fill_circle(x, y, 10, 255, 0, 0)

def bounce_ball(c, x, y):
    # Initialize v_x and v_y with random values within the range of the canvas's width and height
    v_x = random.randint(10, c.width - 10)
    v_y = random.randint(10, c.height - 10)
    
    while True:
        # Clear the canvas
        c.clear(0, 0, 255)
        
        # Draw the ball
        draw_ball(c, x, y)
        
        # Bounce the ball
        bounce_ball(c, x, y)
        
        # Wait for a short time before the next frame
        time.sleep(0.05)

# Example usage
animate_ball(c, 30)
