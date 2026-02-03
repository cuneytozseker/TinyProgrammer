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
def scroll_message():
    while True:
        # Generate a random color
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)

        # Clear the screen
        c.clear(r, g, b)

        # Scroll the message across the screen
        x = c.width // 2 - 100
        y = 0

        while y < c.height:
            c.fill_rect(x, y, c.width, 50, r, g, b)
            y += 10

