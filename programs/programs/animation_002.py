import time
import random
import math

while True:
# Import necessary libraries
from matplotlib import pyplot as plt
from random import randint, uniform

def create_animation(width, height):
    # Set up timer for animation duration
    start = time.time()

    # Generate random numbers between 0 and width -height
    random_num = randint(0, width) + 1
    
    # Create a new frame using the `new` method of the plot object
    frame = plt.figure()
    frame.set_width(width)
    frame.set_height(height)

    # Set up animation loop to display each frame
    frame.mtime += 0.25
    frame.yaxis.linewidth = 1.5
    
    # Generate random numbers and set the colors
    random_num, color = uniform(randint(0, 1), randint(0, 3))

    # Set up animation loop to display each frame
    frame.mtime += 0.25*random_num/width * (random_num / width) + uniform(randint(-random_num - random_num // 4, -random_num + random_num // 4), randint((100, totalWidth))-89)*6
    frame.yaxis.linewidth = color
    
    # Display the plot after an animation loop has run and all frames have been displayed
    plt.show()

# Create a new frame using the `new` method of the plot object
create_animation(10, 5)

def main():
try:
    create_animation(964, 328)
    print("Animated animation finished.")
except Exception as e:
    print(f"Error creating animated animation {e}")
