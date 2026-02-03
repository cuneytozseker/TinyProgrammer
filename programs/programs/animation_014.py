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

def draw_circle(x, y, radius):
    c.fill_circle(x, y, radius, 255, 0, 0)

def draw_line(x1, y1, x2, y2):
    c.line(x1, y1, x2, y2, 255, 0, 0)

def main():
    while True:
        # Clear the canvas
        c.clear(0, 0, 0)
        
        # Draw a circle
        draw_circle(100, 100, 30)
        
        # Draw a line
        draw_line(50, 50, 200, 200)
        
        # Sleep for 2 seconds
        time.sleep(2)
    
    c.close()

