python
import time
import random
import math

c = Canvas()
draw_bouncing_ball()

def draw_bouncing_ball():
    while True:
        # Clear the screen with black background
        c.clear(0, 0, 0)
        
        # Randomly choose a starting position and radius for the ball
        x = random.randint(c.width // 2 - 50, c.width // 2 + 50)
        y = random.randint(c.height // 2 - 50, c.height // 2 + 50)
        radius = random.randint(10, 50)
        
        # Fill the ball with a random color
        c.fill_rect(x, y, radius, radius, 255, 255, 255)
        
        # Move the ball around the screen
        x += random.randint(-1, 1)
        y += random.randint(-1, 1)
        
        # Check if the ball has crossed the canvas edge and reset its position
        if x < 0:
            x = c.width
        elif x > c.width:
            x = 0
        if y < 0:
            y = c.height
        elif y > c.height:
            y = 0
        
        # Sleep for a short time before moving again
        time.sleep(0.1)

# Start drawing the ball
draw_bouncing_ball()
