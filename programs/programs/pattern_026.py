python
import time
import random
from tiny_canvas import Canvas

c = Canvas()

def draw_pattern():
    # Clear the canvas
    c.clear(0, 0, 255)
    
    # Iterate over a range of x and y coordinates
    for i in range(128):
        # Calculate the radius of each circle
        radius = random.randint(10, 30)
        
        # Draw a rectangle with the calculated radius and color
        c.fill_rect(i * 50, i * 50, 480 - 2 * i * 50, 480 - 2 * i * 50, 255, 0, 0)
    
    # Sleep for a short time to create a visually appealing effect
    time.sleep(1)

# Run the draw_pattern function in an infinite loop
while True:
    draw_pattern()
