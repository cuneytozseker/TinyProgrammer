python
import time
import random
import math
from tiny_canvas import Canvas

# Initialize the canvas with size 480x320
c = Canvas(480, 320)

def bounce_ball():
    # Define the initial position and speed of the ball
    x, y = c.width // 2, c.height // 2
    vx, vy = random.uniform(-5, 5), random.uniform(-5, 5)
    
    while True:
        # Clear the canvas
        c.clear(0, 0, 0)
        
        # Draw the ball
        c.fill_circle(x, y, 10, 255, 0, 0, 255)
        
        # Update the position and speed of the ball
        x += vx
        y += vy
        
        # Check for collision with walls
        if x < 0 or x > c.width:
            vx *= -1
        if y < 0 or y > c.height:
            vy *= -1
        
        # Apply gravity
        vy += 0.1
        
        # Sleep for a short period to keep the animation running
        time.sleep(0.01)

# Start the ball bouncing
bounce_ball()
