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

def main():
    c = Canvas()  # Initialize the canvas with dimensions (480, 320)
    
    while True:
        # Generate a random number between -100 and 100 for x and y coordinates
        x = random.randint(-100, 100)
        y = random.randint(-100, 100)
        
        # Fill the rectangle at (x, y) with a random color
        c.fill_rect(x, y, 20, 20, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # Sleep for 1 second
        time.sleep(1)
    
