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

# Define the ball's initial position, radius, and speed
ball_x, ball_y, ball_radius = 100, 50, 20
ball_speed = 3

def animate_ball():
    while True:
        c.clear(0, 0, 0)  # Clear the screen to draw the ball
        c.fill_rect(ball_x, ball_y, ball_radius, ball_radius, 255, 255, 255)  # Draw the ball
        
        # Update the ball's position
        ball_x += ball_speed
        if ball_x > c.width or ball_x < 0:
            ball_speed *= -1  # Reverse the ball's direction

        # Sleep for a short duration to control the animation speed
        time.sleep(0.05)

