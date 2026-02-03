python
import random

def draw_spiral(c):
    # Clear the canvas
    c.clear(0, 0, 255)  # White background

    # Set initial position
    x, y = 200, 150
    r, g, b = 255, 0, 0
    speed = 0.3  # Speed of spiral growth (r decreases with speed)
    angle = random.uniform(0, 360)  # Random starting angle

    while True:
        # Move the circle outward by decreasing radius and increasing angle
        c.pixel(x, y, r, g, b)
        
        # Decrease the radius
        if r > 1:
            r -= speed
        
        # Increase the angle to make the spiral appear more irregular
        angle += random.uniform(-0.1, 0.1)
        
        # Wrap around the circle if the angle exceeds 360 degrees
        if angle >= 360:
            angle = angle % 360

# Start the program
while True:
    draw_spiral(c)
