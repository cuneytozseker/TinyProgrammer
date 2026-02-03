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

c = Canvas()

while True:
    # Get the current time in seconds since the epoch
    current_time = time.time()
    
    # Clear the canvas
    c.clear(0, 0, 0)
    
    # Get the current hour and minute
    hour = int(current_time // (60 * 60))
    minute = int((current_time // 60) % 60)
    
    # Draw the clock face
    c.fill_rect(315, 80, 280, 120, 255, 255, 255)
    c.fill_circle(315, 70, 90, 255, 255, 255)
    
    # Draw the hour hand
    x = (hour * 30) + 90
    y = 80
    c.fill_circle(x, y, 10, 255, 255, 255)
    
    # Draw the minute hand
    x = (minute * 6) + 90
    y = 80
    c.fill_circle(x, y, 10, 255, 255, 255)
    
    # Keep the clock running at a speed of 1 second
    time.sleep(1)

# Clean up and exit
c.clear(0, 0, 0)
print("Clock stopped.")
