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

# Set up the game loop
while True:
    # Clear the screen
    c.clear(0, 0, 0)  # Background color is black

    # Randomly choose a ball's position and size
    x = random.randint(10, 360)
    y = random.randint(10, 240)
    radius = random.randint(5, 30)

    # Fill the ball with white
    c.fill_circle(x, y, radius, 255, 255, 255)

    # Update the screen after a short delay
    time.sleep(1)  # Approximately 1 second

# Stop the game loop
c.close()
