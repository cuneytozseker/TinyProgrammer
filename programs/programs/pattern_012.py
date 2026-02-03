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

def create_pattern(x, y):
    for _ in range(10):  # Pattern duration (in seconds)
        c.clear(x, y)  # Clear the canvas
        c.fill_rect(x, y, 50, 50, 255, 255, 255)  # Fill a large circle with white color
        c.sleep(1)  # Sleep for 1 second

create_pattern(50, 50)
