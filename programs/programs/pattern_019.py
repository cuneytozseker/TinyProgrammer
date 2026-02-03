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

def generate_pattern():
    # Generate a 5x5 pattern of random colors
    c.fill_rect(0, 0, 20, 20, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    time.sleep(1)  # Wait for a second

def main():
    while True:
        generate_pattern()
        c.clear()

