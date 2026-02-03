To create a simple digital clock that updates every second, you can use the `pygame` library and ensure it is run in an infinite loop. Here's the corrected code:

python
import time
import random
import math

from tiny_canvas import Canvas

def draw_clock():
    c.clear(0, 0, 0)
    
    # Calculate the current time in seconds since the epoch
    now = int(time.time())
    
    # Get the hour and minute parts of the current time
    hour = now // 3600
    minute = (now % 3600) // 60
    
    # Draw the hours, minutes, and seconds
    c.fill_rect(10, 10, 200, 50, hour * 36, 0, 255)
    c.fill_rect(400, 10, 200, 50, minute * 6, 0, 255)
    c.fill_rect(800, 10, 200, 50, second * 3, 0, 255)

def main():
    while True:
        draw_clock()
        time.sleep(1)  # Wait for one second

