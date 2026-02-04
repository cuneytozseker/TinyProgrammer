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

# Initialize variables
seconds = 0
x, y, w, h = 120, 320, c.width - 50, c.height - 100
c.clear(0, 0, 0)
c.fill_rect(0, 0, w, h, 255, 255, 255)

# Main infinite loop
while True:
    seconds += 1
    x = math.cos(math.radians(seconds)) * 480
    y = math.sin(math.radians(seconds)) * 320
    c.fill_circle(x, y, 50, 255, 255, 255)
    
    # Clear the canvas after every second
    c.clear(0, 0, 0)
    c.fill_rect(0, 0, w, h, 255, 255, 255)

# Wait for a second before the next loop
time.sleep(1)
