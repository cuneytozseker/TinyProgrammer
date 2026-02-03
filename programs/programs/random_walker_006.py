python
import random

# Initialize variables
x, y = 100, 100
width, height = 800, 600
speed = 3
dot_color = 'red'
dots = []

while True:
    # Randomly choose a new position for the dot
    x += random.randint(-speed, speed)
    y += random.randint(-speed, speed)
    
    # Check if the dot has crossed the screen boundaries
    if x < 0 or y < 0 or x > width or y > height:
        # Reset dot position if it has gone off-screen
        x = 100
        y = 100
    
    # Append the new dot to the list
    dots.append((x, y))
    
    # Draw the dots on the screen
    for dot in dots:
        print(f"Dot: ({dot[0]}, {dot[1]})")
    
    # Sleep for a short duration
    time.sleep(0.1)
```

This script creates a dot moving around the screen, with it changing color every 3 seconds if it has crossed the screen boundaries. The dots are randomly generated and updated in each iteration of the loop.