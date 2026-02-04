python
import time
import random
import math
from tiny_canvas import Canvas

# Main loop to update the clock every second
while True:
    # Get the current time in seconds
    current_time = time.time()

    # Calculate the elapsed time since the last update (in seconds)
    elapsed_time = current_time - last_update

    # Determine if it's time to draw a new time mark
    if elapsed_time >= 1:
        # Get random x and y coordinates for the time mark
        x = random.randint(0, c.width)
        y = random.randint(c.height - 50, c.height)

        # Fill the circle with red color
        c.fill_circle(x, y, 20, 200, 0, 255, 0)

    # Update last update time for the next iteration
    last_update = current_time

    # Refresh the display
    c.refresh()

    # Wait for 1 second before the next update
    time.sleep(1)
