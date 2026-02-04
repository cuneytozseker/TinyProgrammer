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

def draw_bouncing_ball():
    # Set the background color to white
    c.clear(255, 255, 255)
    
    # Loop indefinitely
    while True:
        # Generate a random x and y position for the ball
        x = random.randint(0, c.width - 16)
        y = random.randint(0, c.height - 16)
        
        # Draw a white circle at the current position
        c.fill_circle(x, y, 24, 255, 255, 255)
        
        # Calculate the new position for the ball
        x += random.randint(-3, 3)
        y += random.randint(-3, 3)
        
        # Check if the ball has reached the edges of the canvas
        if x < 0 or y < 0 or x >= c.width or y >= c.height:
            break
        
        # Sleep for a short duration to create motion
        time.sleep(1)

# Call the function to start drawing the ball
draw_bouncing_ball()
