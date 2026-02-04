python
import time
import random
import math
from tiny_canvas import Canvas

# Initialize the canvas with dimensions 480x320
c = Canvas(480, 320)

def bounce_ball(x, y):
    # Calculate the new position of the ball
    dx = random.randint(-1, 1)
    dy = -random.randint(-1, 1)
    
    # Update the ball's coordinates
    x += dx
    y += dy

    # Check if the ball has moved outside the canvas boundaries
    if x < 0 or x > c.width:
        x = 0
    if y < 0 or y > c.height:
        y = 0
    
    return (x, y)

def main():
    while True:
        # Clear the screen
        c.clear(255, 255, 255)
        
        # Update the position of the ball
        (x, y) = bounce_ball(c.width // 2, c.height // 2)
        
        # Draw the ball
        c.fill_circle(x, y, 50, 50, 255, 0, 255)
        
        # Update the screen with the changes
        c.refresh()
        
        # Wait for a short period
        time.sleep(1)


